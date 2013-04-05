# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'URLMap.on_sitemap'
        db.add_column('urlographer_urlmap', 'on_sitemap',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'URLMap.on_sitemap'
        db.delete_column('urlographer_urlmap', 'on_sitemap')


    models = {
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'urlographer.contentmap': {
            'Meta': {'object_name': 'ContentMap'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'options': ('django.db.models.fields.TextField', [], {'default': "'{}'", 'blank': 'True'}),
            'view': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'urlographer.urlmap': {
            'Meta': {'object_name': 'URLMap'},
            'content_map': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['urlographer.ContentMap']", 'null': 'True', 'blank': 'True'}),
            'force_secure': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hexdigest': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'on_sitemap': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'redirect': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'redirects'", 'null': 'True', 'to': "orm['urlographer.URLMap']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'status_code': ('django.db.models.fields.IntegerField', [], {'default': '200', 'db_index': 'True'})
        }
    }

    complete_apps = ['urlographer']