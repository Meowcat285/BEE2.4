from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='BEE2 acceleration',
    ext_modules=cythonize('*.pyx'),
    options={
        'build': {
            'build_lib': '../build_cython/',
        },
    }
)

