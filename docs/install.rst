============
Installation
============

Using pip, preferably in a virtualenv::

    pip install django-urlographer

Add urlographer to INSTALLED_APPS in your project's setup.py::

    INSTALLED_APPS = (
        # ...
        'urlographer',
        # ...
    ) 

Add the following to the end of your project's urls.py::

    urlpatterns += patterns('urlographer.views', ('^.*$', 'route'))


Create the necessary database tables using South_::

    cd /path/to/your/project
    python manage.py migrate urlographer


If you don't have South_ installed (we're not sure why, but trust that you have your reasons), running ``python manage.py syncdb`` in your project directory should also work.

.. _South: http://south.aeracode.org/
