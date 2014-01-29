#!/usr/bin/env python


from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from feedly import __version__, __maintainer__, __email__
import sys

long_description = open('README.md').read()

tests_require = [
    'Django>=1.3',
    'mock',
    'pep8',
    'unittest2',
    'pytest',
]

install_requires = [
    'cqlengine==0.8.72',
    'redis>=2.8.0',
    'celery',
]


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='feedly',
    version=__version__,
    author=__maintainer__,
    author_email=__email__,
    url='http://github.com/tschellenbach/feedly',
    description='Feedly allows you to build complex feed and caching structures using Redis.',
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={'test': tests_require},
    cmdclass={'test': PyTest},
    tests_require=tests_require,
    include_package_data=True,
    dependency_links=[
        'https://github.com/tbarbugli/cqlengine/tarball/0480e38836436a9408c6e57a45b25d48ed835715#egg=cqlengine-0.8.72',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django'
    ],
)
