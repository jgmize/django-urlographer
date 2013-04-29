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

from django.core.urlresolvers import get_mod_func
from django.utils.importlib import import_module
from django.utils.functional import memoize


_view_cache = {}


def force_ascii(s):
    if isinstance(s, unicode):
        return s.encode('ascii', 'ignore')
    else:
        return unicode(s, 'ascii', errors='ignore')


def canonicalize_path(path):
    while '//' in path:
        path = path.replace('//', '/')
    if path.startswith('./'):
        path = path[1:]
    elif path.startswith('../'):
        path = path[2:]
    while '/./' in path:
        path = path.replace('/./', '/')
    while '/../' in path:
        pre, post = path.split('/../', 1)
        if pre.startswith('/') and '/' in pre[1:]:
            pre = '/'.join(pre.split('/')[:-1])
            path = '/'.join([pre, post])
        else:
            path = '/' + post
    return force_ascii(path.lower())


def get_view(lookup_view):
    lookup_view = lookup_view.encode('ascii')
    mod_name, func_or_class_name = get_mod_func(lookup_view)
    assert func_or_class_name != ''
    view = getattr(import_module(mod_name), func_or_class_name)
    assert callable(view) or hasattr(view, 'as_view')
    return view
get_callable = memoize(get_view, _view_cache, 1)


def force_cache_invalidation(request):
    '''
    Returns true if a request from contains the Cache-Control:no-cache header
    '''
    return 'no-cache' in request.META.get('HTTP_CACHE_CONTROL', '')
