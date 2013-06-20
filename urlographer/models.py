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

from hashlib import md5

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django_extensions.db.fields.json import JSONField

from .utils import get_view

# for django memcache backend, 0 means use the default_timeout, but for
# django-redis-cache backend, 0 means no expiration
settings.URLOGRAPHER_CACHE_TIMEOUT = getattr(
    settings, 'URLOGRAPHER_CACHE_TIMEOUT', 0)
settings.URLOGRAPHER_CACHE_PREFIX = getattr(
    settings, 'URLOGRAPHER_CACHE_PREFIX', 'urlographer:')
settings.URLOGRAPHER_INDEX_ALIAS = getattr(
    settings, 'URLOGRAPHER_INDEX_ALIAS', 'index.html')


class ContentMap(models.Model):
    view = models.CharField(max_length=255)
    options = JSONField(blank=True)

    def __unicode__(self):
        return '%s(**%r)' % (self.view, self.options)

    def clean(self):
        try:
            get_view(self.view)
        except:
            raise ValidationError({'view': 'Please enter a valid view.'})

    def save(self, *args, **options):
        self.full_clean()
        super(ContentMap, self).save(*args, **options)
        for urlmap in self.urlmap_set.all():
            cache.set(urlmap.cache_key(), None, 5)


class URLMapManager(models.Manager):
    def cached_get(self, site, path, force_cache_invalidation=False):
        '''
        Use the site and path to construct a temporary URL instance.
        Use that to get the cache key and hexdigest for cache and db queries.
        Set cache if cache miss. Raise NotFoundError if url not in cache or db.
        '''
        url = self.model(site=site, path=path)
        url.set_hexdigest()
        cache_key = url.cache_key()
        if not force_cache_invalidation:
            cached = cache.get(cache_key)
            if cached:
                return cached
        if path.endswith('/') and settings.URLOGRAPHER_INDEX_ALIAS:
            try:
                url = self.get(hexdigest=url.hexdigest)
            except self.model.DoesNotExist:
                url = self.cached_get(
                    site, path + settings.URLOGRAPHER_INDEX_ALIAS,
                    force_cache_invalidation=force_cache_invalidation)
        else:
            url = self.get(hexdigest=url.hexdigest)
        # accessing foreignkeys caches instances with the object
        url.site
        url.content_map
        url.redirect
        cache.set(cache_key, url, timeout=settings.URLOGRAPHER_CACHE_TIMEOUT)
        return url


class URLMap(models.Model):
    site = models.ForeignKey(Site)
    path = models.CharField(max_length=2000)
    force_secure = models.BooleanField(default=False)
    hexdigest = models.CharField(max_length=255, db_index=True, blank=True,
                                 unique=True)
    status_code = models.IntegerField(default=200, db_index=True)
    redirect = models.ForeignKey(
        'self', related_name='redirects', blank=True, null=True)
    content_map = models.ForeignKey(ContentMap, blank=True, null=True)
    on_sitemap = models.BooleanField(default=True, db_index=True)
    objects = URLMapManager()

    def protocol(self):
        if self.force_secure:
            return 'https'
        else:
            return 'http'

    def __unicode__(self):
        return self.protocol() + '://' + self.site.domain + self.path

    def get_absolute_url(self):
        if self.site == Site.objects.get_current():
            return self.path
        else:
            return unicode(self)

    def cache_key(self):
        assert self.hexdigest
        return settings.URLOGRAPHER_CACHE_PREFIX + self.hexdigest

    def set_hexdigest(self):
        self.hexdigest = md5(self.site.domain + self.path).hexdigest()

    def delete(self, *args, **options):
        super(URLMap, self).delete(*args, **options)
        cache.delete(self.cache_key())

    def clean_fields(self, *args, **kwargs):
        try:
            super(URLMap, self).clean_fields(*args, **kwargs)
        except ValidationError, e:
            errors = e.message_dict
        else:
            errors = {}

        if self.redirect and self.redirect == self:
            errors['redirect'] = ['You cannot redirect a url to itself']

        if self.status_code in (301, 302) and not self.redirect:
            errors['redirect'] = ['Status code requires a redirect']

        elif self.status_code == 200 and not self.content_map:
            errors['content_map'] = ['Status code requires a content map']

        if errors:
            raise ValidationError(errors)

    def clean(self):
        self.set_hexdigest()

    def save(self, *args, **options):
        self.full_clean()
        super(URLMap, self).save(*args, **options)
        # accessing foreignkeys caches instances with the object
        self.site
        self.content_map
        self.redirect
        cache.set(self.cache_key(), self,
                  timeout=settings.URLOGRAPHER_CACHE_TIMEOUT)
        if self.path.endswith(settings.URLOGRAPHER_INDEX_ALIAS):
            self._default_manager.cached_get(
                self.site, self.path[:-len(settings.URLOGRAPHER_INDEX_ALIAS)],
                force_cache_invalidation=True)
