"""
This is a collection of meta models to be subclassed in the projects
browser/models.py file.
"""
import os.path as osp

from django.db import models
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


def run_file_path(instance, filename):
    return osp.join('runs', str(instance.run.pk), filename)


class File(RunTagged):
    class Meta:
        abstract = True

    file = models.FileField(upload_to=run_file_path)

    def __init__(self, *args, **kwargs):
        # handle different file objects on construction
        if 'file' in kwargs:
            f = kwargs.pop('file')
            if type(f) == str:
                f = file(f, 'rb+')
            # try convert anything that isnt a file by now into a django File
            # or a django InMemoryUploadedFile
            try:
                if not isinstance(f, file):
                    errmsg = ('If file isnt a file instance, a filename needs '
                              ' to be passed. %r' % f)
                    assert 'filename' in kwargs, errmsg
                    f = InMemoryUploadedFile(f, None, kwargs.pop('filename'),
                                             None, f.len, None)
                else:
                    f = djFile(f)
                f.readable()
            except (TypeError, AttributeError):
                raise TypeError('Cant convert %s to a ' % f +
                                'django.core.files.File instance.')
            kwargs['file'] = f

        super(File, self).__init__(*args, **kwargs)

    def delete(self):
        self.file.delete()
        super(File, self).delete()
