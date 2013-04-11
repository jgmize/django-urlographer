# Copyright 2013 Consumers Unified LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf import settings
from django.contrib.sitemaps.views import sitemap as contrib_sitemap
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sites.models import get_current_site
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import resolve
from django.http import (
    Http404, HttpResponse, HttpResponseNotFound, HttpResponsePermanentRedirect,
    HttpResponseRedirect)

from .models import URLMap
from .utils import canonicalize_path, force_cache_invalidation, get_view

settings.URLOGRAPHER_HANDLERS = getattr(settings, 'URLOGRAPHER_HANDLERS', {})


def route(request):
    if settings.APPEND_SLASH and not request.path_info.endswith('/'):
        # the code below only works if route is mapped to .*
        with_slash = request.path_info + '/'
        if resolve(with_slash)[0] != route:
            return HttpResponsePermanentRedirect(with_slash)
    canonicalized = canonicalize_path(request.path)
    site = get_current_site(request)
    try:
        url = URLMap.objects.cached_get(
            site, canonicalized,
            force_cache_invalidation=force_cache_invalidation(request))
    except URLMap.DoesNotExist:
        url = URLMap(site=site, path=canonicalized, status_code=404)

    request.urlmap = url

    if url.status_code == 200:
        if request.path != canonicalized:
            response = HttpResponsePermanentRedirect(unicode(url))
        else:
            view = get_view(url.content_map.view)
            options = url.content_map.options
            if hasattr(view, 'as_view'):
                initkwargs = options.pop('initkwargs', {})
                response = view.as_view(**initkwargs)(request, **options)
            else:
                response = view(request, **options)
    elif url.status_code == 301:
        response = HttpResponsePermanentRedirect(unicode(url.redirect))
    elif url.status_code == 302:
        response = HttpResponseRedirect(unicode(url.redirect))
    elif url.status_code == 404:
        response = HttpResponseNotFound()
    else:
        response = HttpResponse(status=url.status_code)

    handler = settings.URLOGRAPHER_HANDLERS.get(response.status_code, None)
    if handler:
        if callable(handler) or hasattr(handler, 'as_view'):
            view = handler
        elif isinstance(handler, basestring):
            view = get_view(handler)
        else:
            raise ImproperlyConfigured(
                'URLOGRAPHER_HANDLERS values must be views or import strings')

        if hasattr(view, 'as_view'):
            response = view.as_view()(request, response)
        else:
            response = view(request, response)
    elif response.status_code == 404:
            raise Http404

    return response


def sitemap(request, invalidate_cache=False):
    site = get_current_site(request)
    cache_key = '%s%s_sitemap' % (settings.URLOGRAPHER_CACHE_PREFIX, site)
    if not invalidate_cache and not force_cache_invalidation(request):
        cached = cache.get(cache_key)
        if cached:
            return HttpResponse(content=cached)
    response = contrib_sitemap(
        request,
        {'urlmap': GenericSitemap(
            {'queryset': URLMap.objects.filter(
                site=site, status_code=200, on_sitemap=True)})})
    response.render()
    cache.set(cache_key, response.content, settings.URLOGRAPHER_CACHE_TIMEOUT)
    return response
