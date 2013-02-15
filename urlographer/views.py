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

from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import resolve
from django.http import (
    Http404, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect)

from .models import URLMap
from .utils import canonicalize_path, force_cache_invalidation, get_view


def route(request):
#   the code below only works if route is mapped to .*
#    if not request.path_info.endswith('/'):
#        with_slash = request.path_info + '/'
#        if resolve(with_slash)[0] != route:
#            return HttpResponsePermanentRedirect(with_slash)
    canonicalized = canonicalize_path(request.path)
    site = get_current_site(request)
    try:
        url = URLMap.objects.cached_get(
            site, canonicalized,
            force_cache_invalidation=force_cache_invalidation(request))
    except URLMap.DoesNotExist:
        raise Http404
    if url.status_code == 200:
        if request.path != canonicalized:
            return HttpResponsePermanentRedirect(unicode(url))
        else:
            view = get_view(url.content_map.view)
            options = url.content_map.options
            if hasattr(view, 'as_view'):
                initkwargs = options.pop('initkwargs', {})
                return view.as_view(**initkwargs)(request, **options)
            else:
                return view(request, **options)
    elif url.status_code == 301:
        return HttpResponsePermanentRedirect(unicode(url.redirect))
    elif url.status_code == 302:
        return HttpResponseRedirect(unicode(url.redirect))
    elif url.status_code == 404:
        raise Http404

    return HttpResponse(status=url.status_code)
