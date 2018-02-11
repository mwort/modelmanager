import os.path as osp

from django.contrib import admin
from django.apps import apps
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.safestring import mark_safe

from . import models


def update_functions():
    from django.conf import settings
    project = settings.PROJECT
    # project functions
    pfunctions = [('', f) for f in project.settings.functions.values()]
    # plugin functions
    for p, (_, methods) in settings.PROJECT.settings.plugins.items():
        pfunctions.extend([(p, m) for m in methods.values()])

    for pi, f in pfunctions:
        fentry = models.Function.objects.filter(name=f.name, plugin=pi)
        if len(fentry) > 1:
            print('More than one function registered for %s.%s' % (f.name, pi))
        fentry = fentry.last()
        if fentry is None:
            fo = models.Function(name=f.name, kwargs=(f.kwargs is not None),
                                 doc=f.doc, plugin=pi)
            fo.save()
            # add arguments
            args = [dict(name=n, function=fo)
                    for n in f.positional_arguments]
            args += [dict(name=n, value='%r' % d, function=fo)
                     for n, d in zip(f.optional_arguments, f.defaults)]
            # insert
            for a in args:
                models.Argument(**a).save()
    return


def function_signiture(obj):
    args = ['%s=%s' % (p.name, p.value) for p in obj.argument_set.all()]
    return ', '.join(args)


def plugin(obj):
    return mark_safe('<a href="?plugin={0}">{0}</a>'.format(obj.plugin))


def result(obj):
    if obj.is_configured():
        inpt = '<input type="button" name="%s" value="Run"></input>'
    else:
        inpt = ('<a href="%s/change/"><input type="button" value="Configure">'
                '</input></a>')
    return mark_safe(inpt % obj.id)


class FunctionAdmin(admin.ModelAdmin):
    ordering = ['plugin', 'name']
    list_display = [plugin, 'name', function_signiture, result]
    list_display_links = ['name']
    readonly_fields = ['name', 'plugin', 'doc', 'kwargs']
    inlines = []  # defined as needed in self.get_form
    search_fields = ['plugin', 'name']

    def get_form(self, request, obj=None, **kwargs):
        # due to django admin form fields caching you must
        # redefine inlines on every `get_form()` call
        if (obj):
            self.inlines = []

        if len(obj.argument_set.all()) > 0:
            class ArgumentInlineAdmin(admin.TabularInline):
                model = models.Argument
                extra = 0
                kwargs = obj.kwargs

                def has_add_permission(self, request):
                    """Disable Add another if kwargs=False"""
                    return self.kwargs

                def has_delete_permission(self, request, obj=None):
                    """Disable delete tick box."""
                    return self.kwargs

            self.inlines = [ArgumentInlineAdmin]
        return super(FunctionAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        update_functions()
        return super(FunctionAdmin, self).get_queryset(request)

    def has_add_permission(self, request):
        """Disable Add another if kwargs=False"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable Add another if kwargs=False"""
        return True

    def has_delete_permission(self, request, obj=None):
        """Disable delete tick box."""
        return False


def update_settings():
    from django.conf import settings
    variables = settings.PROJECT.settings.variables
    for vname, value in variables.items():
        fentry = models.Setting.objects.filter(name=vname).last()
        if fentry is None:
            fentry = models.Setting(name=vname, value='%r' % value)
            fentry.save()


class SettingAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_display = ['name', 'value']
    readonly_fields = list_display
    search_fields = ['name', 'value']

    def get_queryset(self, request):
        update_settings()
        return super(SettingAdmin, self).get_queryset(request)

    def has_add_permission(self, request):

        """Disable Add another if kwargs=False"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable Add another if kwargs=False"""
        return True

    def has_delete_permission(self, request, obj=None):
        """Disable delete tick box."""
        return False


admin.site.register(models.Function, FunctionAdmin)
admin.site.register(models.Setting, SettingAdmin)
