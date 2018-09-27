import traceback
import os
import os.path as osp
import sys

from django.conf import settings
from django.http import HttpResponse
from django.contrib.admin.utils import unquote

from .models import Function
from browser.models import Run

# strange behaviour with unquote under PY3
if sys.version_info >= (3, 0):
    def unquote(s):
        return s.replace('_5F', '_')

IMGEXT = ['.jpg', '.png', '.gif', '.svg', '.bmp']
IMGTAG = '<img src="{0}" alt="{0}">'

# list of functions which filter the result of a function
# they all have to take (functionobj, result) as arguments and return the
# result html, if nothing changed the same as the result input must be returned
# functions defined here are appended below
RESULTFILTERS = []

# define global variables for the argument evaluation
ARGUMENTSCOPE = {'project': settings.PROJECT}


def call_run_function(request, rid, fpk):
    run = Run.objects.get(pk=rid)
    fobj = Function.objects.get(pk=unquote(fpk))
    if run and fobj:
        try:
            function = run
            for comp in fpk.split('.'):
                function = getattr(function, comp)
        except AttributeError:
            return HttpResponse(u'%s not found in %s.' % (fpk, run))
        return call_function(fobj, function)
    return HttpResponse(u'Function %s or Run %s not found.' % (fpk, run))


def call_project_function(request, pk):
    fobj = Function.objects.get(pk=unquote(pk))
    function = settings.PROJECT.settings[fobj.name]
    return call_function(fobj, function)


def call_function(fobj, function):
    """
    Handle a project or plugin function call and return output/errors as html.
    """
    # evaluate arguments
    arguments, notset, evalerror = convert_arguments(fobj.argument_set.all())
    errormsg = None
    if len(notset) > 0:
        errormsg = ("<br>Arguments not set: <br>"
                    "<table><tr><th>Name</th><th>Value</th>" +
                    ''.join(['<tr><td>%s:</td><td>%s</td></tr>' % ns
                             for ns in notset.items()]) + '</table>')
    elif len(evalerror) > 0:
        msg = ("<br>Something went wrong while converting the argument: "
               "{0}={1} <pre>{2}</pre><br>Is it valid python code?")
        errormsg = ''.join([msg.format(n, *v) for n, v in evalerror.items()])
    else:
        # evaluate function
        print('Calling %s(**%r)' % (fobj.name, arguments))
        try:
            returned = function(**arguments)
        except Exception:
            finfo = settings.PROJECT.settings.functions[fobj.name]
            errormsg = ("<br>Something isn't right:<pre>{0}</pre><br>Here is "
                        "the function's source code:<br><pre>{1}</pre>"
                        .format(traceback.format_exc(), finfo.code))
    # return error if any
    if errormsg:
        result = errormsg
    else:
        # filter results
        for fltr in RESULTFILTERS:
            result = fltr(fobj, returned)
            if result != returned:
                break
    # make sure unicode string is returned
    return HttpResponse(u'%s' % (result,))


def convert_arguments(args_queryset):
    """
    Try to convert all arguments (django queryset of with strings) and
    return dictionaries of converted arguments, notset and erroreval.
    """
    arguments = {}
    notset = {}
    evalerror = {}
    for a in args_queryset:
        if a.value and a.name:
            try:
                arguments[a.name] = eval(a.value, ARGUMENTSCOPE)
            except Exception:
                evalerror[a.name] = (a.value, traceback.format_exc())
        else:
            notset[a.name] = a.value
    return arguments, notset, evalerror


def is_picture_path(fobj, result):
    project = settings.PROJECT
    tmpdir = project.browser.settings.tmpfilesdir
    # image path
    if type(result) is str and osp.splitext(result)[1] in IMGEXT:
        imgpath = osp.join(project.projectdir, result)
        if osp.exists(imgpath):
            if not osp.realpath(imgpath).startswith(settings.MEDIA_URL):
                newimgpath = osp.join(tmpdir, osp.basename(imgpath))
                os.rename(imgpath, newimgpath)
                imgpath = newimgpath
        else:
            result = 'Cant find: %s' % result
        # valid image found
        result = IMGTAG.format(imgpath)
    return result


def is_matplotlib_figure(fobj, result):
    tmpdir = settings.PROJECT.browser.settings.tmpfilesdir
    # matplotlib Figure instance
    if str(type(result)) == "<class 'matplotlib.figure.Figure'>":
        imgpath = osp.join(tmpdir, fobj.name + '.png')
        result.savefig(imgpath, dpi=200)
        result = IMGTAG.format(imgpath)
    return result


def is_run(fobj, result):
    from ..database.models import Run
    if Run in result.__class__.__mro__:
        return '<a href="/browser/run/%i/change">%s</a>' % (result.pk, result)
    return result


RESULTFILTERS.extend([is_picture_path, is_matplotlib_figure, is_run])
