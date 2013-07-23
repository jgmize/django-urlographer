Modules
===================

:mod:`models` Module
--------------------

.. autoattribute:: urlographer.models.settings.URLOGRAPHER_CACHE_PREFIX

.. autoattribute:: urlographer.models.settings.URLOGRAPHER_CACHE_TIMEOUT

.. note::
    For the memcache backend, 0 means use the default_timeout, but for
    django-redis-cache backend, 0 means no expiration
    (**NOT** recommended)

.. autoattribute:: urlographer.models.settings.URLOGRAPHER_INDEX_ALIAS

.. note::
    This should **not** include the leading '/'

.. autoclass:: urlographer.models.ContentMap
    :members:

.. autoclass:: urlographer.models.URLMapManager
    :members:

.. autoclass:: urlographer.models.URLMap
    :members:

:mod:`utils` Module
-------------------

.. automodule:: urlographer.utils
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`views` Module
-------------------

.. autoattribute:: urlographer.views.settings.URLOGRAPHER_HANDLERS

.. automodule:: urlographer.views
    :members:
    :undoc-members:
    :show-inheritance:
