django-urlographer
==================

A URL mapper for the django web framework

Features:

* supplements the django url resolution
* database + cache driven
* automatic caching and cache invalidation on save
* permanent and temporary redirects
* map url to arbitrary status code
* url canonicalization
    * lowercase
    * ascii
    * eliminate relative paths
    * extra slashes
