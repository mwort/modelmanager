"""
This is a collection of meta models to be subclassed in the projects
browser/models.py file.
"""
import os
import os.path as osp
import shutil

from django.db import models
from django.conf import settings
from django.core.files import File as djFile
from django.core.files.uploadedfile import InMemoryUploadedFile


class Run(models.Model):
    class Meta:
        abstract = True
    time = models.DateTimeField('Time', auto_now_add=True)
    tags = models.CharField(max_length=1024, blank=True, null=True)
    notes = models.TextField('Notes', blank=True)

    def __unicode__(self):
        return u'Run %i' % self.pk


class RunTagged(models.Model):
    class Meta:
        abstract = True
    run = models.ForeignKey('browser.Run', on_delete=models.CASCADE)
    tags = models.CharField(max_length=1024, blank=True, null=True)


class TaggedValue(RunTagged):
    class Meta:
        abstract = True
    MAX_DIGITS = 16
    DECIMAL_PLACES = 8
    name = models.CharField(max_length=128)
    value = models.DecimalField(max_digits=MAX_DIGITS,
                                decimal_places=DECIMAL_PLACES)


def upload_to_path(instance, filename):
    return osp.join(instance.SUBDIR, str(instance.run.pk), filename)


class File(RunTagged):
    class Meta:
        abstract = True

    SUBDIR = 'runs'
    file = models.FileField(upload_to=upload_to_path)

    def __init__(self, *args, **kwargs):
        # handle different file objects on construction
        if 'file' in kwargs:
            kwargs['file'] = self.handle_file(**kwargs)
            if 'filename' in kwargs:
                kwargs.pop('filename')
        super(File, self).__init__(*args, **kwargs)

    def handle_file(self, **kwargs):
        """
        Converts a filepath, a file object or a buffer object to a safe and
        valid django.core.files.File using the kwargs of the __init__.
        """
        f = kwargs['file']
        media_root = settings.MEDIA_ROOT
        if isinstance(f, file) or type(f) is str:
            oldp = osp.abspath(f if type(f) == str else f.name)
            if oldp.startswith(media_root):
                newp = oldp
            else:
                di = osp.join(media_root, self.SUBDIR, str(kwargs['run'].pk))
                newp = osp.join(di, osp.basename(oldp))
                if not osp.exists(di):
                    os.makedirs(di)
                errmsg = "File already exists for this run: " + newp
                assert not osp.exists(newp), errmsg
                shutil.copy(oldp, newp)
            # create django file
            f = djFile(file(newp, 'rb+'))
        else:
            errmsg = ('If file isnt a file instance, a filename needs '
                      ' to be passed. %r' % f)
            assert 'filename' in kwargs, errmsg
            f = InMemoryUploadedFile(f, None, kwargs.pop('filename'),
                                     None, f.len, None)
        return f

    def delete(self):
        self.file.delete()
        super(File, self).delete()
