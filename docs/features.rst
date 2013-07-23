Features
========

* permanent and temporary redirects
* map url to arbitrary status code
* database + cache driven
* automatic caching and cache invalidation on save
* URL canonicalization:
    * case mismatch: (/FOO -> /foo)
    * unicode encoding errors in the path
    * eliminate relative paths (.././../etc)
    * extra slashes (/foo//bar -> /foo/bar)
