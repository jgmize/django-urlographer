from django.contrib import admin
from urlographer.models import URLMap, ContentMap


class URLMapAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'status_code', 'content_map',)
    raw_id_fields = ('redirect', 'content_map')
    readonly_fields = ('hexdigest',)
    search_fields = ('path',)


admin.site.register(URLMap, URLMapAdmin)
admin.site.register(ContentMap)
