from django.http import HttpResponse
from django.views.generic.base import View


def sample_view(request, **kwargs):
    return HttpResponse('test value=' + kwargs['test_val'])


class SampleClassView(View):
    test_val = 'not set'

    def get(self, request, *args, **kwargs):
        return HttpResponse('test value=' + self.test_val)


def sample_handler(request, response):
    response.content = 'modified content'
    return response


class SampleClassHandler(View):
    def get(self, request, response, *args, **kwargs):
        response.content = 'payment required'
        return response
