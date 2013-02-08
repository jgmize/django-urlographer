# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ContentMap'
        db.create_table('urlographer_contentmap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('view', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('options', self.gf('django.db.models.fields.TextField')(default='{}', blank=True)),
        ))
        db.send_create_signal('urlographer', ['ContentMap'])

        # Adding model 'URLMap'
        db.create_table('urlographer_urlmap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'])),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('force_secure', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('hexdigest', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('status_code', self.gf('django.db.models.fields.IntegerField')(default=200)),
            ('redirect', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='redirects', null=True, to=orm['urlographer.URLMap'])),
            ('content_map', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['urlographer.ContentMap'], null=True, blank=True)),
        ))
        db.send_create_signal('urlographer', ['URLMap'])


    def backwards(self, orm):
        # Deleting model 'ContentMap'
        db.delete_table('urlographer_contentmap')

        # Deleting model 'URLMap'
        db.delete_table('urlographer_urlmap')


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
            'hexdigest': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'redirect': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'redirects'", 'null': 'True', 'to': "orm['urlographer.URLMap']"}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'status_code': ('django.db.models.fields.IntegerField', [], {'default': '200'})
        }
    }

    complete_apps = ['urlographer']