from django.conf.urls.defaults import patterns
from django.views.generic.base import View
from urlographer.views import route

urlpatterns = patterns(
    '',
    (r'^test_page/$', View.as_view()),
    (r'^.*$', route),
)
