from django.contrib import admin
from urlographer.models import URLMap, ContentMap


class URLMapAdmin(admin.ModelAdmin):
    raw_id_fields = ('site', 'redirect', 'content_map')


admin.site.register(URLMap, URLMapAdmin)
admin.site.register(ContentMap)
