import collections
import inspect
import logging

import java.lang.Class
from org.python.compiler.ProxyCodeHelpers import AnnotationDescr

log = logging.getLogger(__name__)

class Constant(object):
    """ Use this class to declare class attributes as java const

    Example::

        class Test(BarClamp, Callable, Serializable):

            serialVersionUID = Constant(Long(1234), Long.TYPE)
    """

    def __init__(self, value, type=None):
        # FIXME do type inference on value_type when we have that
        if type is None:
            raise NotImplementedError("type has to be set right now")
        self.value = value
        self.type = type


class ClassInfo(object):
    """
    The ``ClassInfo`` class is used to store Java annotations on a class.
    """

    def __init__(self, cls):
        assert inspect.isclass(cls), "cls:{!r} is not a class.".format(cls)

        self.annotations = []
        self.cls = cls

    def __repr__(self):
        return "<ClassInfo annotations={!r}>".format(self.annotations)

    def annotate(self, _interface, **fields):
        """
        Apply a Java annotation to the class.
        """
        assert isinstance(_interface, java.lang.Class) and _interface.isInterface(), "interface:{!r} is not a Java interface.".format(_interface)

        log.debug("annotate({!r}, {!r})".format(_interface, fields))

        # Store annotation.
        annotation = AnnotationDescr(_interface, fields or None)
        self.annotations.append(annotation)


class MethodInfo(object):
    """
    The ``MethodInfo`` class is used to store Java type information and
    annotations on a method.
    """

    def __init__(self, method, return_type, arg_types, name=None, access=None):
        if isinstance(method, (classmethod, staticmethod)):
            raise NotImplementedError("method:{!r} is not yet supported.".format(method))
        assert inspect.isfunction(method), "method:{!r} is not a function.".format(method)

        assert inspect.isclass(return_type), "return_type:{!r} is not a class.".format(return_type)

        arg_types = tuple(arg_types) if arg_types is not None else ()
        for arg_type in arg_types:
            assert inspect.isclass(arg_type), "arg_type:{!r} is not a class.".format(arg_type)

        argspec = inspect.getargspec(method)
        expect_args = argspec.args[1:]
        assert len(arg_types) == len(expect_args), "method:{!r} has {}, given {}.".format(method, len(expect_args), len(arg_types))

        if not name:
            name = method.__name__
        assert isinstance(name, basestring), "name:{!r} is not a string.".format(name)

        self.access = access
        self.annotations = []
        self.arg_annotations = collections.defaultdict(list)
        self.arg_types = arg_types
        self.exception_types = []
        self.method = method
        self.name = name
        self.return_type = return_type

    def __repr__(self):
        return "<MethodInfo access={!r} annotations={!r} arg_annotations={!r} arg_types={!r} exception_types={!r} name={!r} return_type={!r}>".format(self.access, self.annotations, dict(self.arg_annotations), self.arg_types, self.exception_types, self.name, self.return_type)

    def annotate(self, _interface, **fields):
        """
        Apply a Java annotation to the method.
        """
        assert isinstance(_interface, java.lang.Class) and _interface.isInterface(), "interface:{!r} is not a Java interface.".format(_interface)

        log.debug("annotate({!r}, {!r})".format(_interface, fields))

        # Store annotation.
        annotation = AnnotationDescr(_interface, fields or None)
        self.annotations.append(annotation)

    def annotate_arg(self, _arg, _interface, **fields):
        """
        Apply a Java annotation to the method argument.
        """
        assert isinstance(_arg, basestring), "arg:{!r} is not a string.".format(_arg)
        assert isinstance(_interface, java.lang.Class) and _interface.isInterface(), "interface:{!r} is not a Java interface.".format(_interface)

        argspec = inspect.getargspec(self.method)
        expect_args = argspec.args[1:]
        assert _arg in expect_args, "method:{!r} does not have argument:{!r}.".format(self.method, _arg)

        log.debug("annotate_arg({!r}, {!r}, {!r})".format(_arg, _interface, fields))

        # Store annotation.
        annotation = AnnotationDescr(_interface, fields or None)
        self.arg_annotations[_arg].append(annotation)

    def throws(self, *exception_types):
        """
        Declare what Java exceptions the methods throws.
        """
        for exception_type in exception_types:
            assert inspect.isclass(exception_type), "exception_type:{!r} is not a class.".format(exception_type)

        self.exception_types = exception_types
