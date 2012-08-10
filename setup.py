#!/usr/bin/env python


from setuptools import setup, find_packages
from feedly import __version__, __maintainer__, __email__
long_description = open('README.md').read()

tests_require = [
    'Django>=1.3',
    'mock',
    'pep8',
    'unittest2',
]

install_requires = [
]

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
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='runtests.runtests',
    include_package_data=True,
#    entry_points={
#        'console_scripts': [
#            'raven = raven.scripts.runner:main',
#        ],
#        'paste.filter_app_factory': [
#            'raven = raven.contrib.paste:sentry_filter_factory',
#        ],
#    },
    dependency_links=[
        'http://github.com/tschellenbach/nydus@v10.1.0#egg=nydus==10.1.0',
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
