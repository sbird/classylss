import os
import shutil
from glob import glob
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
import numpy

# base directory of package
package_basedir = os.path.abspath(os.path.dirname(__file__))

def find_version(path, name='version'):
    import re
    s = open(path, 'rt').read()
    version_match = re.search(r"^%s = ['\"]([^'\"]*)['\"]" % name, s, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

CLASS_VERSION = find_version("classylss/version.py", name='class_version')

def build_CLASS(prefix):
    args = (package_basedir, package_basedir, CLASS_VERSION, os.path.abspath(prefix))
    command = 'sh %s/depends/install_class.sh %s %s %s' % args
    ret = os.system(command)
    if ret != 0:
        raise ValueError("Could not build CLASS v%s" % CLASS_VERSION)

class BuildCLib(build_ext):
    """ Custom command to build external C libraries before building extensions """
    def run(self):
        build_CLASS(self.build_temp)
        super().run()

    def build_extensions(self):
        libclass_path = glob(os.path.join(self.build_temp, '*', 'libclass.a'))
        if not libclass_path:
            raise FileNotFoundError("libclass.a not found in expected build directories.")

        for ext in self.extensions:
            ext.extra_objects = libclass_path
            ext.include_dirs.insert(0, os.path.join(self.build_temp, 'include'))
            ext.library_dirs.insert(0, os.path.join(self.build_temp, 'lib'))

        super().build_extensions()

def classy_extension_config():
    return {
        'name': 'classylss.binding',
        'sources': ['classylss/binding.pyx'],
        'include_dirs': [numpy.get_include(),],
        'extra_link_args': ['-g', '-fPIC'],
        'extra_compile_args': ['-g'],
        'language': 'c',
        'libraries': ['class', 'gfortran', 'm'],
    }

setup(
    name='classylss',
    version=find_version("classylss/version.py"),
    author='Nick Hand, Yu Feng',
    author_email='nicholas.adam.hand@gmail.com',
    description="Lightweight Python binding of the CLASS CMB Boltzmann code",
    license='GPL3',
    url="http://github.com/nickhand/classylss",
    install_requires=['numpy', 'Cython'],
    extras_require={'tests': ['pytest', 'astropy', 'scipy']},
    ext_modules=cythonize([Extension(**classy_extension_config())], compiler_directives={'language_level' : "3"}, include_path=[numpy.get_include(), "classylss/"]),
    cmdclass={
        'build_ext': BuildCLib,
        # 'clean': CustomClean
    },
    # package_data = {'classylss': ['*.pxd', '*.pyx']},
    packages=find_packages()
)
