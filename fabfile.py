from fabric.api import local


def publish():
    '''
    Easy publishing of my nice open source project
    '''
    from feedly import __version__
    tag_name = 'v%s' % __version__
    local('python setup.py sdist upload')
    
    local('git tag %s' % tag_name)
    local('git push origin --tags')
