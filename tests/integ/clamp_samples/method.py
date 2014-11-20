from java.io import FileNotFoundException
from java.lang import Integer, Object, String, Void
from org.clamp_supports import StubAnnotation, SingleAnnotation, MultiAnnotation

from clamp.declarative import annotate, clamp_class, method, throws

@clamp_class('org')
class MethodSample(Object):

    @method(Integer.TYPE)
    def returnZero(self):
        return 0

    @method(String)
    def returnFoo(self):
        return 'foo'

    @method(Integer.TYPE, (Integer.TYPE,))
    def returnIntArg(self, arg):
        return arg

    @method(Integer.TYPE, (String, String))
    def returnIntConcat(self, arg1, arg2):
        return int(arg1 + arg2)

    @annotate(StubAnnotation)
    @method(Void.TYPE)
    def stubAnnotation(self):
        pass

    @annotate(SingleAnnotation, value='single')
    @method(Void.TYPE)
    def singleAnnotation(self):
        pass

    @annotate(MultiAnnotation, value='multi')
    @method(Void.TYPE)
    def multiAnnotation(self):
        pass

    @annotate('one', StubAnnotation)
    @annotate('two', SingleAnnotation, value='single')
    @annotate('three', MultiAnnotation, value='multi')
    @method(Void.TYPE, (String, String, String))
    def argAnnotations(self, one, two, three):
        pass

    @throws(FileNotFoundException)
    @method(Void.TYPE)
    def fileNotFound(self):
        raise FileNotFoundException()
