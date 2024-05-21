"""
Setuptools based setup module
"""
from setuptools import setup, find_packages
import versioneer

setup(
    name='ironflow',
    version=versioneer.get_version(),
    description='ironflow - A visual scripting interface for pyiron.',
    long_description='Ironflow combines ryven, ipycanvas and ipywidgets to provide a Jupyter-based visual scripting '
                     'gui for running pyiron workflow graphs.',

    url='https://github.com/pyiron/ironflow',
    author='Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department',
    author_email='liamhuber@greyhavensolutions.com',
    license='BSD',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'ipycanvas',
        'ipython',
        'ipywidgets >= 7,< 8',
        'matplotlib',
        'maggma >= 0.57.1',
        'nglview <= 3.0.9',
        'numpy',
        'owlready2',
        'pyiron_base',
        'pyiron_atomistics',
        'pyiron_gui >= 0.0.8',
        'pyiron_ontology == 0.1.3',
        'ryvencore == 0.3.1.1 ',
        'seaborn',
        'traitlets',
    ],
    cmdclass=versioneer.get_cmdclass(),

    )
