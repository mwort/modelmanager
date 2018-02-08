import traceback
import os
import os.path as osp

from django.conf import settings
from django.http import HttpResponse

from .models import Function

IMGEXT = ['.jpg', '.png', '.gif', '.svg', '.bmp']


def function_call(request, pk):
    """
    Handle a project or plugin function call and return output/errors as html.
    """
    fobj = Function.objects.get(pk=pk)
    project = settings.PROJECT
    function = (project.settings.plugins[fobj.plugin][1][fobj.name]
                if fobj.plugin else project.settings.functions[fobj.name])

    # evaluate arguments
    arguments = {}
    for a in fobj.argument_set.all():
        try:
            aresult = eval(a.value)
        except Exception:
            errormsg = ("Something went wrong while converting the argument:"
                        "%s=%s" % (a.name, a.value) +
                        '<pre>%s</pre>' % traceback.format_exc() +
                        '<br>Make sure it is valid python code.')
            return HttpResponse(errormsg)
        arguments[a.name] = aresult

    # evaluate function
    try:
        result = function(**arguments)
    except Exception:
        result = ("Something isn't right:"
                  '<pre>%s</pre>' % traceback.format_exc() +
                  '<br>Here is the functions source code:<br>'
                  '<pre>%s</pre>' % function.code)

    # evaluate results
    tmpdir = project.browser.settings.tmpfilesdir
    imgtag = '<img src="{0}" alt="{0}">'
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
        result = imgtag.format(imgpath)
    # matplotlib Figure instance
    elif str(type(result)) == "<class 'matplotlib.figure.Figure'>":
        imgpath = osp.join(tmpdir, fobj.name + '.png')
        result.savefig(imgpath, dpi=200)
        result = imgtag.format(imgpath)
    else:
        # parse unicode html
        result = u"%s" % result
    return HttpResponse(result)
