from django.contrib.sites.models import get_current_site
from django.http import (
    Http404, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect)

from .models import URLMap
from .utils import canonicalize_path, get_view


def route(request):
    canonicalized = canonicalize_path(request.path)
    site = get_current_site(request)
    try:
        url = URLMap.objects.cached_get(site, canonicalized)
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
    return HttpResponse(status=url.status_code)
