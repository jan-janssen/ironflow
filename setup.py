"""
Setuptools based setup module
"""
from setuptools import setup, find_packages
import versioneer

setup(
    name='ironflow',
    version=versioneer.get_version(),
    description='ironflow - module extension to pyiron.',
    long_description='http://pyiron.org',

    url='https://github.com/pyiron/ironflow',
    author='Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department',
    author_email='liamhuber@greyhavensolutions.com',
    license='BSD',

    classifiers=['Development Status :: 5 - Production/Stable',
                 'Topic :: Scientific/Engineering :: Physics',
                 'License :: OSI Approved :: BSD License',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9'],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'ipycanvas',
        'ipython',
        'ipywidgets >= 7,< 9',
        'matplotlib',
        'nglview',
        'numpy',
        'pyiron_base',
        'pyiron_atomistics >= 0.2.57',
        'ryvencore'
    ],
    cmdclass=versioneer.get_cmdclass(),

    )
