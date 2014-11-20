package org.clamp_supports;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(RetentionPolicy.RUNTIME)
public @interface MultiAnnotation {
    String value();
    String extra() default "";
}
