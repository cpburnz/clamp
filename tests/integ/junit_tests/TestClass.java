import java.lang.reflect.*;
import org.junit.Test;
import static org.junit.Assert.*;
import org.python.compiler.MTime;

import org.clamp_samples.class_.StubAnnotationSample;
import org.clamp_samples.class_.SingleAnnotationSample;
import org.clamp_samples.class_.MultiAllAnnotationSample;
import org.clamp_samples.class_.MultiDefaultAnnotationSample;
import org.clamp_supports.StubAnnotation;
import org.clamp_supports.SingleAnnotation;
import org.clamp_supports.MultiAnnotation;

public class TestClass {
    @Test
    public void testStubAnnotationSample() throws Exception {
        StubAnnotation anno = StubAnnotationSample.class.getAnnotation(StubAnnotation.class);
        assertNotNull(anno);
    }

    @Test
    public void testSingleAnnotationSample() throws Exception {
        SingleAnnotation anno = SingleAnnotationSample.class.getAnnotation(SingleAnnotation.class);
        assertNotNull(anno);
        assertEquals(anno.value(), "single");
    }

    @Test
    public void testMultiAllAnnotationSample() throws Exception {
        MultiAnnotation anno = MultiAllAnnotationSample.class.getAnnotation(MultiAnnotation.class);
        assertNotNull(anno);
        assertEquals(anno.value(), "all");
        assertEquals(anno.extra(), "test");
    }

    @Test
    public void testMultiDefaultAnnotationSample() throws Exception {
        MultiAnnotation anno = MultiDefaultAnnotationSample.class.getAnnotation(MultiAnnotation.class);
        assertNotNull(anno);
        assertEquals(anno.value(), "default");
        assertEquals(anno.extra(), "");
    }
}
