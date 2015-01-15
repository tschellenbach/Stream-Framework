__author__ = 'Thierry Schellenbach'
__copyright__ = 'Copyright 2012, Thierry Schellenbach'
__credits__ = ['Thierry Schellenbach, mellowmorning.com, @tschellenbach']


__license__ = 'BSD'
__version__ = '0.11.4'
__maintainer__ = 'Thierry Schellenbach'
__email__ = 'thierryschellenbach@gmail.com'
__status__ = 'Production'


import warnings


message = '''
Feedly has been renamed to Stream Framework. The new package is available on PYPI as stream_framework.
The new stream_framework package is backwards compatible with Feedly. Please upgrade before 22-01-2015, after which the feedly
package will be removed from pypi. Read more about it in this blog post:
https://www.tumblr.com/blog/getstream
'''
warnings.warn(message, DeprecationWarning)