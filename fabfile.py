from fabric.api import local, cd
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


def publish(test='yes'):
    '''
    Easy publishing of my nice open source project
    '''
    if test == 'yes':
        validate()

    from stream_framework import __version__
    tag_name = 'v%s' % __version__
    local('python setup.py sdist upload')

    local('git tag %s' % tag_name)
    local('git push origin --tags')


def validate():
    with cd(PROJECT_ROOT):
        local('pep8 --exclude=migrations --ignore=E501,E225,W293 stream_framework')
        # local('pyflakes -x W stream_framework')
        local(
            'py.test -sl --tb=short --cov coveralls --cov-report html --cov stream_framework stream_framework/tests')


def clean():
    # all dirs which contain python code
    python_dirs = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        python_dir = any(f.endswith('.py') for f in files)
        if python_dir:
            python_dirs.append(root)
    for d in python_dirs:
        local('bash -c "autopep8 -i %s/*.py"' % d)


def docs():
    local('DJANGO_SETTINGS_MODULE=stream_framework.tests.settings pandoc -s -w rst README.md -o docs/readme.rst')
    local('sphinx-build -Eav docs html')
