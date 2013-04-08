from celery.decorators import task
from django.test.client import RequestFactory

from urlographer.views import sitemap


@task(ignore_result=True)
def update_sitemap_cache():
    factory = RequestFactory()
    request = factory.get('/sitemap.xml')
    sitemap(request, invalidate_cache=True)
