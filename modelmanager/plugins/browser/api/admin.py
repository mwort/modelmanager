# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from django.urls import reverse

from . import models


def function(obj):
    change_url = reverse('admin:api_function_change',
                         args=(admin.utils.quote(obj.pk),))
    is_configured = obj.is_configured()
    if is_configured:
        ln = '<a name="{i}" href="#" action="call">{n}</a>'
    else:
        ln = '<a href="{cu}">{n}</a>'
    elm = ln.format(i=obj.pk, cu=change_url, n=obj.name)
    return mark_safe(elm)


def configured(obj):
    change_url = reverse('admin:api_function_change',
                         args=(admin.utils.quote(obj.pk),))
    ny = 'yes' if obj.is_configured() else 'no'
    imgurl = static('admin/img/icon-%s.svg' % ny)
    sln = '&ensp;<a href="{cu}"><img src="{iu}" alt="True"></a>'
    return mark_safe(sln.format(cu=change_url, iu=imgurl))


def update_functions():
    from django.conf import settings

    for pi, f in settings.PROJECT.settings.functions.items():
        fentry = models.Function.objects.filter(name=pi)
        if len(fentry) > 1:
            print('More than one function registered for %s' % pi)
        fentry = fentry.last()
        if fentry is None:
            fo = models.Function(name=pi, kwargs=(f.kwargs is not None),
                                 doc=f.doc)
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


@admin.register(models.Function)
class FunctionAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_display = [function, configured]
    readonly_fields = ['signiture', "description"]
    exclude = ['name', 'doc', 'kwargs']
    inlines = []  # defined as needed in self.get_form
    search_fields = ['name']

    def get_form(self, request, obj=None, **kwargs):
        # due to django admin form fields caching you must
        # redefine inlines on every `get_form()` call
        if (obj):
            self.inlines = []

        if len(obj.argument_set.all()) > 0 or obj.kwargs:
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
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def signiture(self, obj):
        sign = ['%s=%s' % (p.name, p.value) for p in obj.argument_set.all()]
        if obj.kwargs:
            sign += ['**kw']
        return mark_safe('<pre>%s(%s)</pre>' % (obj.name, ', '.join(sign)))

    def description(self, obj):
        return mark_safe('<pre>%s</pre>' % obj.doc)


@admin.register(models.Setting)
class SettingAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_display = ['name', 'value']
    readonly_fields = list_display
    search_fields = ['name', 'value']

    def get_queryset(self, request):
        self.update()
        return super(SettingAdmin, self).get_queryset(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def update(self):
        from django.conf import settings
        variables = settings.PROJECT.settings.variables
        for vname, value in variables.items():
            fentry = models.Setting.objects.filter(name=vname).last()
            if fentry and fentry.value != '%r' % value:
                fentry = None
            if fentry is None:
                fentry = models.Setting(name=vname, value='%r' % value)
                fentry.save()
        return
