from fabric.api import local, cd
from facebook_example.settings import BASE_ROOT
import os
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_ROOT, '../'))


def publish(test='yes'):
    '''
    Easy publishing of my nice open source project
    '''
    if test == 'yes':
        validate()

    local('git push')

    from feedly import __version__
    tag_name = 'v%s' % __version__
    local('python setup.py sdist upload')

    local('git tag %s' % tag_name)
    local('git push origin --tags')


def validate():
    with cd(PROJECT_ROOT):
        local('pep8 --exclude=migrations --ignore=E501,E225 feedly')
        local('pyflakes.py -x W feedly')
        #local('python -m unittest feedly.tests')


def clean():
    local('bash -c "autopep8 -i *.py"')
    local('bash -c "autopep8 -i feedly/*.py"')
    local('bash -c "autopep8 -i feedly/aggregators/*.py"')
    local('bash -c "autopep8 -i feedly/feed_managers/*.py"')
    local('bash -c "autopep8 -i feedly/feeds/*.py"')
    local('bash -c "autopep8 -i feedly/serializers/*.py"')
    local('bash -c "autopep8 -i feedly/structures/*.py"')
    local('bash -c "autopep8 -i feedly/test_utils/*.py"')
    local('bash -c "autopep8 -i feedly/verbs/*.py"')
