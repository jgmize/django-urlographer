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
