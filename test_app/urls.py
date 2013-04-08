from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import View

from urlographer.views import route

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    (r'^test_page/$', View.as_view()),
    (r'^.*$', route),
)
urlpatterns += staticfiles_urlpatterns()
