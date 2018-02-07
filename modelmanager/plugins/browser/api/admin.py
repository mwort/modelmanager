import os.path as osp
import inspect

from django.contrib import admin
from django.apps import apps
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from . import models
from modelmanager.api import Function


class ArgumentInlineAdmin(admin.TabularInline):
    model = models.Argument
    extra = 0

    def has_add_permission(self, request):
        """Disable Add another if kwargs=False"""
        return False


def signiture(obj):
    args = ['%s=%s' % (p.name, p.value) for p in obj.argument_set.all()]
    return ', '.join(args)


class FunctionAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_display = ['name', signiture, 'doc']
    readonly_fields = ['name', 'kwargs', 'doc', 'plugin']
    inlines = [ArgumentInlineAdmin]
    search_fields = ['name']

    def get_queryset(self, request):
        # update functions
        from django.conf import settings
        func = settings.PROJECT.settings.functions
        for fname, f in func.items():
            fi = Function(f)
            fentry = models.Function.objects.filter(name=fi.name).last()
            if fentry is None:
                fentry = models.Function(name=fname, kwargs=fi.kwargs,
                                         doc=fi.doc)
                fentry.save()
            for aname, default in fi.arguments:
                aentry = models.Argument.objects.filter(name=aname, function=fentry).last()
                if aentry is None:
                    atype = models.TYPES[type(default)] if default else 'str'
                    aentry = models.Argument(name=aname, value=default,
                                             function=fentry, type=atype)
                    aentry.save()
        return super(FunctionAdmin, self).get_queryset(request)


class SettingAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_display = ['name', 'value']
    readonly_fields = list_display
    search_fields = ['name', 'value']

    def get_queryset(self, request):
        # update functions
        from django.conf import settings
        variables = settings.PROJECT.settings.variables
        for vname, value in variables.items():
            fentry = models.Setting.objects.filter(name=vname).last()
            if fentry is None:
                fentry = models.Setting(name=vname, value='%r' % value)
                fentry.save()
        return super(SettingAdmin, self).get_queryset(request)


admin.site.register(models.Function, FunctionAdmin)
admin.site.register(models.Setting, SettingAdmin)
