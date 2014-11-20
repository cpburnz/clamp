import java.io.FileNotFoundException;
import java.lang.String;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import org.junit.Test;
import static org.junit.Assert.*;

import org.clamp_samples.method.MethodSample;
import org.clamp_supports.StubAnnotation;
import org.clamp_supports.SingleAnnotation;
import org.clamp_supports.MultiAnnotation;

public class TestMethod {

    @Test
    public void testReturnZero() throws Exception {
        MethodSample methodObj = new MethodSample();
        assertEquals(0, methodObj.returnZero());
    }

    @Test
    public void testReturnFoo() throws Exception {
        MethodSample methodObj = new MethodSample();
        assertEquals("foo", methodObj.returnFoo());
    }

    @Test
    public void testReturnIntArg() throws Exception {
        MethodSample methodObj = new MethodSample();
        assertEquals(0, methodObj.returnIntArg(0));
        assertEquals(1234, methodObj.returnIntArg(1234));
        assertEquals(-1234, methodObj.returnIntArg(-1234));
    }

    @Test
    public void testReturnIntConcat() throws Exception {
        MethodSample methodObj = new MethodSample();
        assertEquals(0, methodObj.returnIntConcat("0", "0"));
        assertEquals(123456, methodObj.returnIntConcat("123", "456"));
    }

    @Test
    public void testStubAnnotation() throws Exception {
        Method method = MethodSample.class.getDeclaredMethod("stubAnnotation");
        assertNotNull(method);

        StubAnnotation anno = method.getAnnotation(StubAnnotation.class);
        assertNotNull(anno);
    }

    @Test
    public void testSingleAnnotation() throws Exception {
        Method method = MethodSample.class.getDeclaredMethod("singleAnnotation");
        assertNotNull(method);

        SingleAnnotation anno = method.getAnnotation(SingleAnnotation.class);
        assertNotNull(anno);
        assertEquals(anno.value(), "single");
    }

    @Test
    public void testMultiAnnotation() throws Exception {
        Method method = MethodSample.class.getDeclaredMethod("multiAnnotation");
        assertNotNull(method);

        MultiAnnotation anno = method.getAnnotation(MultiAnnotation.class);
        assertNotNull(anno);
        assertEquals(anno.value(), "multi");
        assertEquals(anno.extra(), "");
    }

    @Test
    public void testArgAnnotations() throws Exception {
        Method method = MethodSample.class.getDeclaredMethod("argAnnotations", String.class, String.class, String.class);
        assertNotNull(method);
        Annotation[][] argAnnos = method.getParameterAnnotations();
        assertEquals(argAnnos.length, 3);

        assertEquals(argAnnos[0].length, 1);
        StubAnnotation stubAnno = (StubAnnotation)argAnnos[0][0];
        assertNotNull(stubAnno);

        assertEquals(argAnnos[1].length, 1);
        SingleAnnotation singleAnno = (SingleAnnotation)argAnnos[1][0];
        assertNotNull(singleAnno);
        assertEquals(singleAnno.value(), "single");

        assertEquals(argAnnos[2].length, 1);
        MultiAnnotation multiAnno = (MultiAnnotation)argAnnos[2][0];
        assertNotNull(multiAnno);
        assertEquals(multiAnno.value(), "multi");
        assertEquals(multiAnno.extra(), "");
    }

    @Test(expected=FileNotFoundException.class)
    public void testFileNotFound() throws Exception {
        Method method = MethodSample.class.getDeclaredMethod("fileNotFound");
        Class<?>[] exceptions = method.getExceptionTypes();
        assertEquals(exceptions.length, 1);
        assertEquals(exceptions[0], FileNotFoundException.class);

        MethodSample methodObj = new MethodSample();
        methodObj.fileNotFound();
    }
}
