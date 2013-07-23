=====
Usage
=====

.. _url-mapping:
Mapping a URL to a view
-----------------------

Create a :class:`~urlographer.models.ContentMap` with the view and
options specified, then create an :class:`~urlographer.models.URLMap`
with a status_code of 200 and the content_map FK pointing to the
:class:`~urlographer.models.ContentMap` you just created.


Creating redirects
------------------

Create an :class:`~urlographer.models.URLMap` with the "redirect" FK
pointing to another URLMap (usually one that has already been mapped to
a view, as detailed in :ref:`url-mapping`) the redirect target and a
status_code of 301 or 302, depending on whether you want a permanent or
temporary redirect.


Returning an arbitrary status code
----------------------------------

The status_code field on a :class:`~urlographer.models.URLMap` can be
be set to an arbitrary integer. This can be useful, for example, to
explicitly mark a resource as no longer available by setting the 
status_code field to 410_.

.. _410: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.11
