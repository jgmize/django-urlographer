from django.contrib import admin
from urlographer.models import URLMap, ContentMap


class URLMapAdmin(admin.ModelAdmin):
    raw_id_fields = ('redirect', 'content_map')
    readonly_fields = ('hexdigest',)


admin.site.register(URLMap, URLMapAdmin)
admin.site.register(ContentMap)
