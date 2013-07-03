from django.test.client import RequestFactory


class RequestMock(RequestFactory):

    '''
    Didn't see another solution for this. Decided to read some snippets
    and modded them into the requestfactory class
    http://www.mellowmorning.com/2011/04/18/mock-django-request-for-testing/
    '''

    def request(self, **request):
        from django.core.handlers.base import BaseHandler
        "Construct a generic request object."
        request['REQUEST'] = dict()
        request = RequestFactory.request(self, **request)
        handler = BaseHandler()
        handler.load_middleware()
        for middleware_method in handler._request_middleware:
            if middleware_method(request):
                raise Exception("Couldn't create request mock object - "
                                "request middleware returned a response")
        return request
