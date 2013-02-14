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
from django.core import validators
from django.db import models
from django_extensions.db.fields.json import JSONField

from .utils import get_view

# for django memcache backend, 0 means use the default_timeout, but for
# django-redis-cache backend, 0 means no expiration
CACHE_TIMEOUT = getattr(settings, 'URLOGRAPHER_CACHE_TIMEOUT', 0)
CACHE_PREFIX = getattr(settings, 'URLOGRAPHER_CACHE_PREFIX', 'urlographer:')


class ContentMap(models.Model):
    view = models.CharField(max_length=255)
    options = JSONField(blank=True)

    def save(self, *args, **options):
        assert get_view(self.view)
        super(ContentMap, self).save(*args, **options)


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
        url = self.get(hexdigest=url.hexdigest)
        cache.set(cache_key, url, timeout=CACHE_TIMEOUT)
        return url


class URLMap(models.Model):
    site = models.ForeignKey(Site)
    path = models.CharField(max_length=2000)
    force_secure = models.BooleanField(default=False)
    hexdigest = models.CharField(max_length=255, db_index=True, blank=True)
    status_code = models.IntegerField(default=200)
    redirect = models.ForeignKey(
        'self', related_name='redirects', blank=True, null=True)
    content_map = models.ForeignKey(ContentMap, blank=True, null=True)
    objects = URLMapManager()

    def protocol(self):
        if self.force_secure:
            return 'https'
        else:
            return 'http'

    def __unicode__(self):
        return self.protocol() + '://' + self.site.domain + self.path

    def cache_key(self):
        assert self.hexdigest
        return CACHE_PREFIX + self.hexdigest

    def set_hexdigest(self):
        self.hexdigest = md5(self.site.domain + self.path).hexdigest()

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
        cache.set(self.cache_key(), self, timeout=CACHE_TIMEOUT)
