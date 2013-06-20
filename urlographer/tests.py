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

from django.conf import settings
from django.contrib.sites.models import get_current_site, Site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import Http404, HttpResponse, HttpRequest
from django.test.client import RequestFactory
from override_settings import override_settings
from test_extensions import TestCase
from urlographer import models, tasks, sample_views, utils, views
import mox


class ContentMapTest(TestCase):
    def test_save_existing_view(self):
        content_map = models.ContentMap(view='urlographer.views.route')
        self.assertEqual(content_map.clean(), None)

    def test_save_nonexistent_view(self):
        content_map = models.ContentMap(view='urlographer.views.nonexistent')
        self.assertRaisesMessage(
            ValidationError, 'Please enter a valid view.', content_map.clean)

    def test_save(self):
        content_map = models.ContentMap.objects.create(
            view='urlographer.views.route')
        models.URLMap.objects.create(
            site=Site.objects.get(id=1), path='/test_path',
            content_map=content_map)
        # infinite recursion FTW
        mock = mox.Mox()
        mock.StubOutWithMock(models.ContentMap, 'full_clean')
        mock.StubOutWithMock(models.URLMap, 'cache_key')
        mock.StubOutWithMock(models.cache, 'set')
        models.ContentMap.full_clean()
        models.URLMap.cache_key().AndReturn('urlmap_key')
        models.cache.set('urlmap_key', None, 5)

        mock.ReplayAll()
        content_map.save()
        mock.VerifyAll()
        mock.UnsetStubs()
        self.assertEqual(content_map.id, 1)

    def test_unicode(self):
        content_map = models.ContentMap(
            view='urlographer.views.route', options={'article_id': 3})
        self.assertEqual(
            unicode(content_map),
            "urlographer.views.route(**{'article_id': 3})")


class URLMapTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.url = models.URLMap(site=self.site, path='/test_path')
        self.hexdigest = '389661d2e64f9d426ad306abe6e8f957'
        self.cache_key = settings.URLOGRAPHER_CACHE_PREFIX + self.hexdigest
        self.mox = mox.Mox()
        self.mox.StubOutWithMock(models.URLMapManager, 'cached_get')

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_protocol(self):
        self.assertEqual(self.url.protocol(), 'http')

    def test_https_protocol(self):
        self.url.force_secure = True
        self.assertEqual(self.url.protocol(), 'https')

    def test_unicode(self):
        self.assertEqual(unicode(self.url), u'http://example.com/test_path')

    def test_get_absolute_url(self):
        self.assertEqual(self.url.get_absolute_url(), '/test_path')

    def test_get_absolute_url_other_site(self):
        self.url.site = Site(domain='other.com')
        self.assertEqual(self.url.get_absolute_url(),
                         'http://other.com/test_path')

    def test_https_unicode(self):
        self.url.force_secure = True
        self.assertEqual(unicode(self.url), u'https://example.com/test_path')

    def test_set_hexdigest(self):
        self.assertFalse(self.url.hexdigest)
        self.url.set_hexdigest()
        self.assertEqual(
            self.url.hexdigest, self.hexdigest)

    def test_save(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 204
        self.assertFalse(self.url.id)
        self.assertFalse(self.url.hexdigest)
        self.mox.StubOutWithMock(models.cache, 'set')
        models.cache.set(
            self.cache_key, self.url,
            timeout=settings.URLOGRAPHER_CACHE_TIMEOUT)
        self.mox.ReplayAll()
        self.url.save()
        self.mox.VerifyAll()
        self.assertEqual(self.url.hexdigest, self.hexdigest)
        self.assertEqual(self.url.id, 1)

    def test_save_validates(self):
        self.url.status_code = 200
        self.assertRaisesMessage(
            ValidationError, 'Status code requires a content map',
            self.url.save)

    def test_save_perm_redirect_wo_redirect_raises(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 301
        self.assertRaisesMessage(
            ValidationError, 'Status code requires a redirect', self.url.save)

    def test_save_temp_redirect_wo_redirect_raises(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 302
        self.assertRaisesMessage(
            ValidationError, 'Status code requires a redirect', self.url.save)

    def test_save_redirect_to_self_raises(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 301
        self.url.redirect = self.url
        self.assertRaisesMessage(
            ValidationError, 'You cannot redirect a url to itself',
            self.url.save)

    def test_save_200_wo_content_map_raises(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 200
        self.assertRaisesMessage(
            ValidationError, 'Status code requires a content map',
            self.url.save)

    def test_save_data_invalid_for_field_definition_raises(self):
        self.url.path = 'x' * 2001
        self.url.status_code = 404
        m = 'Ensure this value has at most 2000 characters (it has 2001).'
        self.assertRaisesMessage(ValidationError, m, self.url.save)

    def test_delete_deletes_cache(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 204
        self.url.save()
        self.mox.StubOutWithMock(models.cache, 'delete')
        models.cache.delete(self.url.cache_key())
        self.mox.ReplayAll()
        self.url.delete()
        self.mox.VerifyAll()
        self.assertFalse(self.url.id)

    def test_unique_hexdigest(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 204
        self.url.save()
        self.url.id = None
        self.assertRaisesMessage(
            ValidationError,
            u'Url map with this Hexdigest already exists.',
            self.url.save)

    @override_settings(URLOGRAPHER_INDEX_ALIASES=['index.html'])
    def test_save_index_refreshes_slash_cache(self):
        urlmap = models.URLMap(
            site=self.site, path='/test/index.html', status_code=204)
        models.URLMapManager.cached_get(
            self.site, '/test/', force_cache_invalidation=True)
        self.mox.ReplayAll()
        urlmap.save()
        self.mox.VerifyAll()



class URLMapManagerTest(TestCase):
    def setUp(self):
        self.site = Site(domain='example.com')
        self.url = models.URLMap(site=self.site, path='/test_path')
        self.hexdigest = '389661d2e64f9d426ad306abe6e8f957'
        self.cache_key = settings.URLOGRAPHER_CACHE_PREFIX + self.hexdigest
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_cached_get_cache_hit(self):
        self.mox.StubOutWithMock(models.cache, 'get')
        models.cache.get(self.cache_key).AndReturn(self.url)
        self.mox.ReplayAll()
        url = models.URLMap.objects.cached_get(self.site, self.url.path)
        self.mox.VerifyAll()
        self.assertEqual(url, self.url)

    def test_cached_get_cache_miss(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 204
        self.url.save()
        self.mox.StubOutWithMock(models.cache, 'get')
        self.mox.StubOutWithMock(models.cache, 'set')
        models.cache.get(self.cache_key)
        models.cache.set(
            self.cache_key, self.url,
            timeout=settings.URLOGRAPHER_CACHE_TIMEOUT)
        self.mox.ReplayAll()
        url = models.URLMap.objects.cached_get(self.site, self.url.path)
        self.mox.VerifyAll()
        self.assertEqual(url, self.url)

    def test_cached_get_does_not_exist(self):
        self.mox.StubOutWithMock(models.cache, 'get')
        models.cache.get(self.cache_key)
        self.mox.ReplayAll()
        self.assertRaises(
            models.URLMap.DoesNotExist, models.URLMap.objects.cached_get,
            self.site, self.url.path)
        self.mox.VerifyAll()

    def test_cached_get_force_cache_invalidation(self):
        self.site.save()
        self.url.site = self.site
        self.url.status_code = 204
        self.url.save()
        self.mox.StubOutWithMock(models.cache, 'get')
        self.mox.StubOutWithMock(models.cache, 'set')
        models.cache.set(
            self.cache_key, self.url,
            timeout=settings.URLOGRAPHER_CACHE_TIMEOUT)
        self.mox.ReplayAll()
        url = models.URLMap.objects.cached_get(
            self.site, self.url.path, force_cache_invalidation=True)
        self.mox.VerifyAll()
        self.assertEqual(url, self.url)

    @override_settings(URLOGRAPHER_INDEX_ALIASES=['index.html'])
    def test_cached_get_index_alias_cache_hit(self):
        index_urlmap = models.URLMap(site=self.site, path='/index.html',
                                     status_code=204)
        index_urlmap.set_hexdigest()
        index_key = settings.URLOGRAPHER_CACHE_PREFIX + index_urlmap.hexdigest
        root_key = (settings.URLOGRAPHER_CACHE_PREFIX +
                    '617a9471507f0eb608f3858291adb70f')
        self.mox.StubOutWithMock(models.cache, 'get')
        models.cache.get(root_key)
        models.cache.get(index_key).AndReturn(index_urlmap)
        self.mox.ReplayAll()
        urlmap = models.URLMap.objects.cached_get(self.site, '/')
        self.mox.VerifyAll()
        self.assertEqual(urlmap, index_urlmap)


class RouteTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = Site.objects.get()
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_route_not_found(self):
        request = self.factory.get('/404')
        self.assertEqual(request.path, '/404')
        self.assertRaises(Http404, views.route, request)

    def test_route_gone(self):
        models.URLMap.objects.create(
            site=self.site, status_code=410, path='/410')
        request = self.factory.get('/410')
        response = views.route(request)
        self.assertEqual(response.status_code, 410)

    def test_route_set_not_found(self):
        models.URLMap.objects.create(
            site=self.site, status_code=404, path='/404')
        request = self.factory.get('/404')
        self.assertRaises(Http404, views.route, request)

    def test_route_redirect_canonical(self):
        content_map = models.ContentMap(
            view='django.views.generic.base.TemplateView')
        content_map.options['initkwargs'] = {
            'template_name': 'admin/base.html'}
        content_map.save()
        models.URLMap.objects.create(site=self.site, path='/test',
                                     content_map=content_map)
        response = views.route(self.factory.get('/TEST'))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response._headers['location'][1],
                         'http://example.com/test')

    def test_permanent_redirect(self):
        target = models.URLMap.objects.create(
            site=self.site, path='/target', status_code=204)
        models.URLMap.objects.create(
            site=self.site, path='/source', redirect=target, status_code=301)
        response = views.route(self.factory.get('/source'))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response._headers['location'][1],
                         'http://example.com/target')

    def test_redirect(self):
        target = models.URLMap.objects.create(
            site=self.site, path='/target', status_code=204)
        models.URLMap.objects.create(
            site=self.site, path='/source', redirect=target, status_code=302)
        response = views.route(self.factory.get('/source'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response._headers['location'][1],
                         'http://example.com/target')

    def test_content_map_class_based_view(self):
        content_map = models.ContentMap(
            view='urlographer.sample_views.SampleClassView')
        content_map.options['initkwargs'] = {
            'test_val': 'testing 1 2 3'}
        content_map.save()
        models.URLMap.objects.create(
            site=self.site, path='/test', content_map=content_map)
        response = views.route(self.factory.get('/test'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'test value=testing 1 2 3')

    def test_content_map_view_function(self):
        content_map = models.ContentMap(
            view='urlographer.sample_views.sample_view')
        content_map.options['test_val'] = 'testing 1 2 3'
        content_map.save()
        urlmap = models.URLMap.objects.create(
            site=self.site, path='/test', content_map=content_map)
        request = self.factory.get('/test')
        response = views.route(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'test value=testing 1 2 3')
        self.assertEqual(request.urlmap, urlmap)

    def test_force_cache_invalidation(self):
        path = '/test'
        request = self.factory.get(path)
        site = get_current_site(request)
        url_map = models.URLMap(site=site, path=path, status_code=204)
        self.mox.StubOutWithMock(views, 'force_cache_invalidation')
        self.mox.StubOutWithMock(models.URLMapManager, 'cached_get')
        views.force_cache_invalidation(request).AndReturn(True)
        models.URLMapManager.cached_get(
            site, path, force_cache_invalidation=True).AndReturn(
                url_map)
        self.mox.ReplayAll()
        response = views.route(request)
        self.assertEqual(response.status_code, 204)

    def test_append_slash_redirect(self):
        response = self.client.get('/test_page')
        self.assertRedirects(response, '/test_page/', status_code=301,
                             target_status_code=405)

    @override_settings(APPEND_SLASH=False)
    def test_append_slash_off_no_redirect(self):
        response = self.client.get('/test_page')
        self.assertEqual(response.status_code, 404)

    def test_append_slash_w_slash_no_match(self):
        response = self.client.get('/fake_page')
        self.assertEqual(response.status_code, 404)

    @override_settings(
        URLOGRAPHER_HANDLERS={
            403: 'urlographer.sample_views.sample_handler'})
    def test_handler_as_string(self):
        models.URLMap.objects.create(
            site=self.site, path='/page', status_code=403)
        response = views.route(self.factory.get('/page'))
        self.assertContains(response, 'modified content', status_code=403)

    @override_settings(
        URLOGRAPHER_HANDLERS={
            206: sample_views.sample_handler})
    def test_handler_as_func(self):
        models.URLMap.objects.create(
            site=self.site, path='/page', status_code=206)
        response = views.route(self.factory.get('/page'))
        self.assertContains(response, 'modified content', status_code=206)

    @override_settings(
        URLOGRAPHER_HANDLERS={
            402: sample_views.SampleClassHandler})
    def test_handler_as_class(self):
        models.URLMap.objects.create(
            site=self.site, path='/page', status_code=402)
        response = views.route(self.factory.get('/page'))
        self.assertContains(response, 'payment required', status_code=402)

    @override_settings(
        URLOGRAPHER_HANDLERS={
            404: {'test': 'this'}})
    def test_handler_as_dict_fails(self):
        models.URLMap.objects.create(
            site=self.site, path='/page', status_code=404)
        self.assertRaisesMessage(
            ImproperlyConfigured,
            'URLOGRAPHER_HANDLERS values must be views or import strings',
            views.route, self.factory.get('/page'))


class CanonicalizePathTest(TestCase):
    def test_lower(self):
        self.assertEqual(utils.canonicalize_path('/TEST'), '/test')

    def test_slashes(self):
        self.assertEqual(utils.canonicalize_path('//t//e///s/t'),
                         '/t/e/s/t')

    def test_dots(self):
        self.assertEqual(
            utils.canonicalize_path('./../this/./is/./only/../a/./test.html'),
            '/this/is/a/test.html')
        self.assertEqual(
            utils.canonicalize_path('../this/./is/./only/../a/./test.html'),

            '/this/is/a/test.html')

    def test_non_ascii(self):
        self.assertEqual(utils.canonicalize_path(u'/te\xa0\u2013st'), '/test')


class ForceCacheInvalidationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_header_not_set(self):
        self.assertFalse(utils.force_cache_invalidation(self.factory.get('/')))

    def test_header_set(self):
        request = self.factory.get('/')
        request.META.update({'HTTP_CACHE_CONTROL': 'no-cache'})
        self.assertTrue(utils.force_cache_invalidation(request))


class SitemapTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mox = mox.Mox()
        self.mox.StubOutWithMock(views, 'force_cache_invalidation')
        self.mox.StubOutWithMock(views.URLMap.objects, 'filter')
        self.mox.StubOutWithMock(views, 'contrib_sitemap')
        self.mox.StubOutWithMock(views, 'GenericSitemap')
        self.mox.StubOutWithMock(views.cache, 'get')
        self.mox.StubOutWithMock(views.cache, 'set')
        self.site = Site.objects.get_current()
        self.cache_key = '%s%s_sitemap' % (
            settings.URLOGRAPHER_CACHE_PREFIX, self.site)
        self.request = self.factory.get('/sitemap.xml')
        self.mock_contrib_sitemap_response = HttpResponse(
            content='<mock>Sitemap</mock>')
        self.mock_contrib_sitemap_response.render = lambda: None
        self.mox.StubOutWithMock(self.mock_contrib_sitemap_response, 'render')

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_get_cache_miss(self):
        views.force_cache_invalidation(self.request)
        views.cache.get(self.cache_key)
        views.URLMap.objects.filter(
            site=self.site, status_code=200, on_sitemap=True).AndReturn(
                'mock queryset')
        views.GenericSitemap({'queryset': 'mock queryset'}).AndReturn(
            'mock GenericSitemap')
        self.mock_contrib_sitemap_response.render()
        views.contrib_sitemap(
            self.request, {'urlmap': 'mock GenericSitemap'}).AndReturn(
                self.mock_contrib_sitemap_response)
        views.cache.set(
            self.cache_key, self.mock_contrib_sitemap_response.content,
            settings.URLOGRAPHER_CACHE_TIMEOUT)
        self.mox.ReplayAll()
        response = views.sitemap(self.request)
        self.mox.VerifyAll()
        self.assertEqual(
            response.content, self.mock_contrib_sitemap_response.content)

    def test_get_cache_hit(self):
        views.force_cache_invalidation(self.request)
        views.cache.get(self.cache_key).AndReturn(
            self.mock_contrib_sitemap_response.content)
        self.mox.ReplayAll()
        response = views.sitemap(self.request)
        self.mox.VerifyAll()
        self.assertEqual(
            response.content, self.mock_contrib_sitemap_response.content)

    def test_get_force_cache_invalidation(self):
        views.force_cache_invalidation(self.request).AndReturn(True)
        views.URLMap.objects.filter(
            site=self.site, status_code=200, on_sitemap=True).AndReturn(
                'mock queryset')
        views.GenericSitemap({'queryset': 'mock queryset'}).AndReturn(
            'mock GenericSitemap')
        views.contrib_sitemap(
            self.request, {'urlmap': 'mock GenericSitemap'}).AndReturn(
                self.mock_contrib_sitemap_response)
        self.mock_contrib_sitemap_response.render()
        views.cache.set(
            self.cache_key, self.mock_contrib_sitemap_response.content,
            settings.URLOGRAPHER_CACHE_TIMEOUT)
        self.mox.ReplayAll()
        response = views.sitemap(self.request)
        self.mox.VerifyAll()
        self.assertEqual(
            response.content, self.mock_contrib_sitemap_response.content)

    def test_get_invalidate_cache(self):
        views.URLMap.objects.filter(
            site=self.site, status_code=200, on_sitemap=True).AndReturn(
                'mock queryset')
        views.GenericSitemap({'queryset': 'mock queryset'}).AndReturn(
            'mock GenericSitemap')
        views.contrib_sitemap(
            self.request, {'urlmap': 'mock GenericSitemap'}).AndReturn(
                self.mock_contrib_sitemap_response)
        self.mock_contrib_sitemap_response.render()
        views.cache.set(
            self.cache_key, self.mock_contrib_sitemap_response.content,
            settings.URLOGRAPHER_CACHE_TIMEOUT)
        self.mox.ReplayAll()
        response = views.sitemap(self.request, invalidate_cache=True)
        self.mox.VerifyAll()
        self.assertEqual(
            response.content, self.mock_contrib_sitemap_response.content)


class UpdateSitemapCacheTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_update_sitemap_cache(self):
        self.mox.StubOutWithMock(tasks, 'sitemap')
        tasks.sitemap(mox.IsA(HttpRequest), invalidate_cache=True)
        self.mox.ReplayAll()
        tasks.update_sitemap_cache()
        self.mox.VerifyAll()
