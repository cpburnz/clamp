# Declarative should do all type inference, etc, in
# ClampProxyMakerMeta (other than of course class decorator)

from clamp.proxymaker import ClampProxyMaker
from clamp.signature import Constant

def clamp_base(package, proxy_maker=ClampProxyMaker):
    """ A helper method that allows you to create clamped classes

    Example::

        BarClamp = clamp_base(package='bar')


        class Test(BarClamp, Callable, Serializable):

            def __init__(self):
                print "Being init-ed", self

            def call(self):
                print "foo"
                return 42
    """

    def _clamp_closure(package, proxy_maker):
        """This closure sets the metaclass with our desired attributes
        """
        class ClampProxyMakerMeta(type):

            def __new__(cls, name, bases, dct):
                newdct = dict(dct)
                newdct['__proxymaker__'] = proxy_maker(package=package)
                return type.__new__(cls, name, bases, newdct)

        return ClampProxyMakerMeta


    class ClampBase(object):
        """Allows us not to have to set the __metaclass__ at all"""
        __metaclass__ = _clamp_closure(package=package, proxy_maker=proxy_maker)

    return ClampBase



import inspect
import logging

from clamp.signature import ClassInfo, MethodInfo

log = logging.getLogger(__name__)

def clamp_class(package, proxy_maker=ClampProxyMaker):
    """
    Clamp a class and rewrite as a Java class.

    Example::

        @clamp_class('org.example.package')
        class PythonClass(object):
            ...
    """
    assert isinstance(package, basestring), "package:{!r} is not a string.".format(package)

    def class_decorator(target):
        log.debug("clamp_class({!r}, {!r})({!r})".format(package, proxy_maker, target))
        assert inspect.isclass(target), "target:{!r} is not a class.".format(target)

        # Check to see if the class was compiled by the default proxy maker.
        # Format:
        #
        #   org.python.proxies.<module>$<Class>$<x>
        #   org.python.proxies.<package>.<module>$<Class>$<x>
        #

        try:
            target_package, target_module = target.__module__.rsplit('.', 1)
        except IndexError:
            proxy_package = 'org.python.proxies'
            proxy_module = target.__module__
            proxy_class = target.__name__
        else:
            proxy_package = 'org.python.proxies.' + target_package
            proxy_module = target_module
            proxy_class = target.__name__

        log.debug("Find proxy base: {}:{}:{}".format(proxy_package, proxy_module, proxy_class))

        log.debug("{}".format(target))
        bases = []
        for base in target.__bases__:
            log.debug("- {}".format(base))
            if base.__module__ == proxy_package and tuple(base.__name__.split('$')[:-1]) == (proxy_module, proxy_class):
                # Found proxy base, extract its bases.
                for sub_base in base.__bases__:
                    log.debug("  - {}".format(sub_base))
                    bases.append(sub_base)
            else:
                # Normal base.
                bases.append(base)

        log.debug(bases)

        class ClampProxyMakerMeta(type):

            def __new__(mcs, name, bases, dct):
                log.debug("ClampProxyMakerMeta({!r}, {!r}, {!r})".format(name, bases, dct))
                newdct = dict(dct)
                newdct['__metaclass__'] = mcs
                newdct['__proxymaker__'] = proxy_maker(package=package)
                return type.__new__(mcs, name, bases, newdct)

        # Clamp class.
        return ClampProxyMakerMeta(target.__name__, tuple(bases), dict(vars(target)))

    return class_decorator

def annotate(*args, **fields):
    """
    Apply a Java annotation to a Python class or method.

    Example::

        @annotate(JavaIterface, field1="Value 1", ...)
        class PythonClass(object):

            @annotate(JavaInterface, field1="Value 1", ...)
            def pythonMethod(self):
                ...

            @annotate('arg', JavaInterface, field1="Value 1", ...)
            def doSomething(self, arg):
                ...
    """
    if len(args) == 1:
        interface = args[0]
        return _annotate(interface, fields)
    elif len(args) == 2:
        arg, interface = args
        return _annotate_arg(arg, interface, fields)

    raise TypeError("annotate() takes either 1 or 2 positional arguments ({} given).".format(len(args)))

def _annotate(interface, fields):

    def annotate_decorator(target):
        log.debug("annotate({!r}, {!r})({!r})".format(interface, fields, target))

        assert inspect.isclass(target) or inspect.isfunction(target), "target:{!r} is not a class or method.".format(target)

        if inspect.isclass(target):
            if not hasattr(target, '_clamp'):
                target._clamp = ClassInfo(target)
            info = target._clamp
        elif inspect.isfunction(target):
            # Require methods to be decorated with @method in order to detect
            # missing type information early.
            assert hasattr(target, '_clamp'), "method:{!r} has not been decorated with @method.".format(target)
            info = target._clamp

        # Add annotation.
        info.annotate(interface, **fields)

        return target

    return annotate_decorator

def _annotate_arg(arg, interface, fields):

    def annotate_decorator(method):
        log.debug("annotate({!r}, {!r}, {!r})({!r})".format(arg, interface, fields, method))
        method._clamp.annotate_arg(arg, interface, **fields)
        return method

    return annotate_decorator

def method(return_type, arg_types=None, name=None, access=None):
    """
    Apply Java type information the method. This is required in order to
    expose any Python methods in a clamped class.

    Example::

        @method(java.lang.Void)
        def doNothing(self):
            pass

        @method(java.lang.String, (java.lang.Long, java.lang.Long))
        def someMethod(self, value1, value2):
            return str(value1 + value2)
    """
    def method_decorator(method):
        log.debug("method({!r}, {!r}, {!r})({!r})".format(return_type, arg_types, name, method))
        method._clamp = MethodInfo(method, return_type, arg_types=arg_types, name=name, access=access)
        return method

    return method_decorator

def throws(*exception_types):
    """
    Declare what Java exceptions the method throws.

    Example::

        @throws(java.io.FileNotFoundException)
        @method(java.lang.Void.TYPE)
        def doNothing(self):
            pass
    """
    def throws_decorator(method):
        log.debug("throws(*{!r})({!r})".format(exception_types, method))
        method._clamp.throws(*exception_types)
        return method

    return throws_decorator
