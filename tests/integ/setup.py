import ez_setup
ez_setup.use_setuptools()

import sys
import os
import zipfile

from setuptools import setup, find_packages, Command
from glob import glob

# add parent clamp path
sys.path.append("../../")

from clamp.commands import clamp_command


from org.junit.runner import JUnitCore
from javax.tools import ToolProvider
from java.io import File
from java.net import URLClassLoader
from java.net import URL


class test_command(Command):

    description = "Run junit tests"
    user_options = [
        ("tempdir=",   "t", "temporary directory for test data"),
        ("junit-testdir=",   "j", "directory containing junit tests")
    ]

    def initialize_options(self):
        self.tempdir = 'build/tmp'
        self.junit_testdir = 'junit_tests'

    def finalize_options(self):
        self.testjar = os.path.join(self.tempdir, 'tests.jar')
        self.test_classesdir = os.path.join(self.tempdir, 'classes')
        self.supportjar = os.path.join(self.tempdir, 'support.jar')
        self.support_classesdir = os.path.join(self.tempdir, 'support_classes')
        self.support_sourcesdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clamp_supports')

    def build_jar(self):
        build_jar_cmd = self.distribution.get_command_obj('build_jar')
        build_jar_cmd.output = os.path.join(self.testjar)
        self.run_command('build_jar')

    def build_support_jar(self):
        with zipfile.ZipFile(self.supportjar, 'w') as fh:
            for path, _dirs, files in os.walk(self.support_classesdir):
                for fname in files:
                    fh.write(os.path.join(path, fname), os.path.relpath(os.path.join(path, fname), self.support_classesdir))

    def import_support_jar(self):
        addURL = URLClassLoader.getDeclaredMethod('addURL', [URL])
        addURL.accessible = True
        addURL.invoke(URLClassLoader.getSystemClassLoader(), [File(os.path.abspath(self.supportjar)).toURL()])

    def get_classpath(self):
        jython_dir = os.path.split(os.path.split(sys.executable)[0])[0]
        junit = glob(os.path.join(jython_dir, 'javalib/junit-*.jar'))[0]

        return ":".join([os.path.join(jython_dir, sys.JYTHON_DEV_JAR),
                         junit, self.supportjar, self.testjar])

    def get_support_classpath(self):
        jython_dir = os.path.split(os.path.split(sys.executable)[0])[0]
        junit = glob(os.path.join(jython_dir, 'javalib/junit-*.jar'))[0]

        return ":".join([os.path.join(jython_dir, sys.JYTHON_DEV_JAR), junit])

    def get_test_classes(self):
        urls = [URL('file:' + os.path.abspath(self.test_classesdir) + '/'),
                URL('file:' + os.path.abspath(self.testjar))]
        urls.extend(URLClassLoader.getSystemClassLoader().getURLs())
        loader = URLClassLoader(urls)

        for fname in [name for name in self.get_java_files() if 'test' in name.lower()]:
            classname = os.path.splitext(fname)[0]
            yield loader.loadClass(classname)

    def get_java_files(self):
        return [fname for fname in os.listdir(self.junit_testdir) if fname.endswith('java')]

    def get_support_files(self):
        return [os.path.relpath(os.path.join(path, fname), self.support_sourcesdir) for path, _dirs, files in os.walk(self.support_sourcesdir) for fname in files if fname.endswith('.java')]

    def run_javac(self):
        javac = ToolProvider.getSystemJavaCompiler()
        for fname in self.get_java_files():
            err = javac.run(None, None, None, ['-cp', self.get_classpath(), '-d', self.test_classesdir,
                                               os.path.join(self.junit_testdir, fname)])
            if err:
                sys.exit()

    def run_support_javac(self):
        javac = ToolProvider.getSystemJavaCompiler()
        for fname in self.get_support_files():
            destdir = os.path.join(self.support_classesdir, os.path.dirname(fname))
            self.mkpath(destdir)
            err = javac.run(None, None, None, ['-cp', self.get_support_classpath(), '-d', destdir,
                                                 os.path.join(self.support_sourcesdir, fname)])

    def run_junit(self):
        result = JUnitCore.runClasses(list(self.get_test_classes()))
        print "Ran {} tests in {}s, failures: {}".format(result.runCount, result.runTime, result.failureCount)

        if result.failures:
            print "Failures:"
            for failure in result.failures:
                print failure

    def run(self):
        self.mkpath(self.support_classesdir)
        self.run_support_javac()
        self.build_support_jar()
        self.import_support_jar()
        self.mkpath(os.path.join(self.tempdir, 'classes'))
        self.build_jar()
        self.run_javac()
        self.run_junit()


setup(
    name = "clamp-tests",
    version = "0.1",
    packages = find_packages(),
    clamp = {
        "modules": ["clamp_samples"]
    },
    cmdclass = { "install": clamp_command,
                 "test": test_command}
)

