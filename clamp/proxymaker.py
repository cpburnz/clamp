import inspect
import logging
import re

import java
from java.io import Serializable
from java.lang.reflect import Modifier
from org.python.core import Py
from org.python.compiler import CustomMaker, ProxyCodeHelpers
from org.python.util import CodegenUtils

from clamp.build import get_builder
from clamp.signature import Constant

_MATCH_PRIVATE_NAME = re.compile('^_(?P<class>\w+)__(?P<attribute>\w+)$')

log = logging.getLogger(__name__)


class SerializableProxyMaker(CustomMaker):

    # FIXME and push in docs presumably - in general, unless user otherwise specifies,
    # serialVersionUID of 1 is OK for python, thanks to dynamic
    # typing. Other errors -not having the right interface support
    # - will be caught earlier anyway.

    # NOTE: SerializableProxyMaker is itself a java proxy, but it's not a custom one!

    # TODO support fields in conjunction with property support in Python

# (None,
#  array(java.lang.Class, [<type 'java.util.concurrent.Callable'>, <type 'java.io.Serializable'>]),
#  u'BarClamp',
#  u'__main__',
#  u'clamped.__main__.BarClamp',
#  {'__init__': <function __init__ at 0x2>, '__module__': '__main__', 'call': <function call at 0x3>, '__proxymaker__': <clamp.ClampProxyMaker object at 0x4>}, 'clamped', {})

    def __init__(self, superclass, interfaces, className, pythonModuleName, fullProxyName, mapping, package, kwargs):
        self.mapping = mapping
        self.package = package
        self.kwargs = kwargs

        log.debug("superclass=%s, interfaces=%s, className=%s, pythonModuleName=%s, fullProxyName=%s, mapping=%s, "
                  "package=%s, kwargs=%s", superclass, interfaces, className, pythonModuleName, fullProxyName, mapping,
                  package, kwargs)

        # FIXME break this out
        is_serializable = False
        inheritance = list(interfaces)
        if superclass:
            inheritance.append(superclass)
        for cls in inheritance:
            if issubclass(cls, Serializable):
                is_serializable = True

        if is_serializable:
            self.constants = { "serialVersionUID" : (java.lang.Long(1), java.lang.Long.TYPE) }
        else:
            self.constants = {}
        if "constants" in kwargs:
            self.constants.update(self.kwargs["constants"])
        self.updateConstantsFromMapping(mapping)

        CustomMaker.__init__(self, superclass, interfaces, className, pythonModuleName, fullProxyName, mapping)

    def updateConstantsFromMapping(self, mapping):
        """Looks for Constant in Object's dict and updates the constants, with appropriate values
        """
        for key, val in mapping.iteritems():
            if isinstance(val, Constant):
                if key in self.constants:
                    log.warn("Constant with name %s is already declared, overriding", key)
                self.constants[key] = (val.value, val.type)

    def doConstants(self):
        # FIXME eg, self.constants = { "fortytwo": (java.lang.Long(42), java.lang.Long.TYPE) }
        log.debug("Constants: %s", self.constants)
        code = self.classfile.addMethod("<clinit>", ProxyCodeHelpers.makeSig("V"), Modifier.STATIC)
        for constant, (value, constant_type) in sorted(self.constants.iteritems()):
            self.classfile.addField(
                constant,
                CodegenUtils.ci(constant_type), Modifier.PUBLIC | Modifier.STATIC | Modifier.FINAL)
            code.visitLdcInsn(value)
            code.putstatic(self.classfile.name, constant, CodegenUtils.ci(constant_type))
        code.return_()

    def saveBytes(self, bytes):
        get_builder().write_class_bytes(self.package, self.myClass, bytes)

    def makeClass(self):
        builder = get_builder()
        log.debug("Entering makeClass for %r", self)
        try:
            import sys
            log.debug("Current sys.path: %s", sys.path)
            # If already defined on sys.path (including CLASSPATH), simply return this class
            # if you need to tune this, derive accordingly from this class or create another CustomMaker
            cls = Py.findClass(self.myClass)
            log.debug("Looked up proxy: %r, %r", self.myClass, cls)
            if cls is None:
                raise TypeError("No proxy class")
        except:
            if builder:
                log.debug("Calling super... for %r", self.package)
                cls = CustomMaker.makeClass(self)
                log.info("Built proxy: %r", self.myClass)
            else:
                raise TypeError("Cannot clamp proxy class {} without a defined builder".format(self.myClass))
        return cls

    def visitClassAnnotations(self):
        # Find class annotations.
        class_info = self.mapping.get('_clamp')
        if class_info is not None:
            for annotation in class_info.annotations:
                self.addClassAnnotation(annotation)

    def visitMethods(self, *args):
        # Only override the signature:
        #
        #   void visitMethods()
        #
        if args:
            return self.super__visitMethods(*args)

        # Add default methods.
        self.super__visitMethods()

        # Add methods with type information.
        for name, method in self.mapping.iteritems():
            if isinstance(method, (classmethod, staticmethod)):
                log.warning("method:{!r} is not yet supported.".format(method))
                continue

            if not inspect.isfunction(method):
                continue

            method_info = getattr(method, '_clamp', None)
            if method_info is None:
                continue

            if method_info.return_type is None or method_info.arg_types is None:
                log.warning("method:{!r} info:{!r} is missing type information.".format(method, method_info))
                continue

            if method_info.access is not None:
                access = method_info.access
            else:
                # Deduce method modifer from name and decorators.
                # - TODO: How should @classmethod be handled? Should it be STATIC?
                access = access_from_name(name)

                if isinstance(method, staticmethod):
                    # Interpret:
                    #
                    #   @staticmethod
                    #   def func(...)
                    #
                    # As:
                    #
                    #   static func(...)
                    #
                    access |= Modifier.STATIC

                if getattr(method, '__isabstractmethod__', False):
                    # Interpret:
                    #
                    #   @abc.abstractmethod
                    #   def func(self, ...)
                    #
                    # As:
                    #
                    #   abstract func(...)
                    #
                    access |= Modifier.ABSTRACT

            # Slice off the beginning *self* argument.
            # - TODO: This will need to be modified once @staticmethod and
            #   @classmethod are supported.
            argspec = inspect.getargspec(method)
            args = argspec.args[1:]

            arg_annotations = [method_info.arg_annotations[arg] for arg in args]

            # HACK: This causes the methods to be generated without a call to
            # the super-class. This prevents a `NullPointerException` from
            # being raised because of a lack of passing the non-existant
            # class.
            access |= Modifier.ABSTRACT

            self.addMethod(method_info.name, name, method_info.return_type, method_info.arg_types, method_info.exception_types, access, None, method_info.annotations, arg_annotations)


class ClampProxyMaker(object):

    def __init__(self, package, **kwargs):
        self.package = package
        self.kwargs = kwargs

    def __call__(self, superclass, interfaces, className, pythonModuleName, fullProxyName, mapping):
        """Constructs a usable proxy name that does not depend on ordering"""
        log.debug("Called ClampProxyMaker: %s, %r, %r, %s, %s, %s, %r", self.package, superclass, interfaces,
                  className, pythonModuleName, fullProxyName, mapping)
        return SerializableProxyMaker(
            superclass, interfaces, className, pythonModuleName,
            self.package + "." + pythonModuleName + "." + className, mapping,
            self.package, self.kwargs)


def access_from_name(name):
    """
    Derive the method or field access from its name.
    """
    result = _MATCH_PRIVATE_NAME.match(name)
    if result is not None:
        # Interpret:
        #
        #   def __func(self, ...)
        #
        # As:
        #
        #   private __func(...)
        #
        return Modifier.PRIVATE

    elif name.startswith('__') and name.endswith('__'):
        # Interpret:
        #
        #   def __func__(self, ...)
        #
        # As:
        #
        #   public __func__(...)
        #
        return Modifier.PUBLIC

    elif name.startswith('_'):
        # Interpret:
        #
        #   def _func(self, ...)
        #
        # As:
        #
        #   protected _func(...)
        #
        return Modifier.PROTECTED

    else:
        # Interpret:
        #
        #   def func(self, ...)
        #
        # As:
        #
        #   public func(...)
        #
        return Modifier.PUBLIC
