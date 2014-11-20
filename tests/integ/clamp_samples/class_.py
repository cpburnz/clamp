from java.lang import Object
from org.clamp_supports import StubAnnotation, SingleAnnotation, MultiAnnotation

from clamp.declarative import annotate, clamp_class

@clamp_class('org')
@annotate(StubAnnotation)
class StubAnnotationSample(Object):
    pass

@clamp_class('org')
@annotate(SingleAnnotation, value='single')
class SingleAnnotationSample(Object):
    pass

@clamp_class('org')
@annotate(MultiAnnotation, value='all', extra='test')
class MultiAllAnnotationSample(Object):
    pass

@clamp_class('org')
@annotate(MultiAnnotation, value='default')
class MultiDefaultAnnotationSample(Object):
    pass
