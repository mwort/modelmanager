# -*- coding: utf-8 -*-
"""
The global Django admin browser configuration.
"""
from __future__ import unicode_literals
import csv
import os.path as osp

from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from ..api import admin as api_admin

try:
    import StringIO as io
except ImportError:
    import io


def export_to_csv(modeladmin, request, queryset):
    """
    Action to export a queryset to csv file.

    Only PY2.7 supported, converting everything to str.
    """
    buf = io.StringIO()
    headers = [str(f.name) for f in queryset.model._meta.fields]
    writer = csv.writer(buf)
    writer.writerow(headers)

    for obj in queryset:
        row = []
        for field in headers:
            val = getattr(obj, field)
            row.append(str(val))
        writer.writerow(row)
    buf.seek(0)
    response = HttpResponse(buf, content_type='text/csv')
    content = ('attachment; filename=%s.csv'
               % queryset.model._meta.verbose_name_raw)
    response['Content-Disposition'] = content
    return response


def file_preview_field(field):
    img = u'<img style="max-height:100px;"src="{url}" />'
    href = u'<a href="{url}">{content}</a>'

    def file(obj):
        ffi = getattr(obj, field.name)
        if osp.splitext(ffi.url)[1] in ['.jpg', '.png']:
            elem = href.format(url=ffi.url, content=img.format(url=ffi.url))
        else:
            elem = href.format(url=ffi.url, content=ffi.name)
        return elem
    file.allow_tags = True
    return file


class DefaultModelAdmin(admin.ModelAdmin):
    ordering = ['-id']
    actions = [export_to_csv]

    def get_list_display(self, request):
        meta = self.model._meta
        fields = meta.fields
        if hasattr(self.model, 'show_columns'):
            field_names = self.model.show_columns
        else:
            field_names = [f.name for f in fields]
        # fields for special fields
        for f in fields:
            if f.get_internal_type() == 'ForeignKey':
                field_names[field_names.index(f.name)] = related_model_link(f)
            if f.get_internal_type() == 'FileField':
                field_names[field_names.index(f.name)] = file_preview_field(f)
        return field_names

    def get_list_display_links(self, request, list_display):
        return list_display

    def get_search_fields(self, request):
        return self.list_display

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if not f.editable]

    @property
    def inlines(self):
        return [make_default_inline(m.related_model)
                for m in self.model._meta.related_objects]

    @property
    def list_filter(self):
        return simple_filter_fields(self.model._meta.fields)


def simple_filter_fields(fields):
    filterable = ("BooleanField CharField DateField DateTimeField "
                  "IntegerField ForeignKey ManyToManyField".split())
    return [f.name for f in fields if f.get_internal_type() in filterable]


def make_default_inline(ilmodel):
    class DefaultInlineAdmin(admin.TabularInline):
        model = ilmodel
        classes = ['collapse']
        extra = 0
    return DefaultInlineAdmin


def related_model_link(field):
    def link_fk(obj):
        relmodel = getattr(obj, field.name)
        href = '<b><a href="{}">{}</a></b>'
        urlname = ("admin:%s_%s_change" % (relmodel._meta.app_label,
                   relmodel._meta.verbose_name_raw))
        url = reverse(urlname, args=(relmodel.pk,))
        return mark_safe(href.format(url, relmodel.pk))
    link_fk.short_description = field.name
    return link_fk


class RunAdmin(DefaultModelAdmin):
    """Admin that also shows file_interface functions."""

    def change_view(self, request, object_id, form_url='', extra_context=None):
        run = self.model.objects.get(id=object_id)
        api_admin.update_functions()
        functions = run.get_file_interface_functions()
        extra_context = extra_context or {}
        res = [(api_admin.function(f), api_admin.configured(f))
               for f in functions]
        extra_context['results'] = res
        return super(RunAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context)
