from django.views.generic.base import View

def sample_handler(request, response):
    response.content = 'modified content'
    return response


class SampleClassHandler(View):
    def get(self, request, response, *args, **kwargs):
        response.content = 'payment required'
        return response
