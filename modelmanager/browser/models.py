from django.db import models


class Run(models.Model):
    class Meta:
        abstract = True
        ordering = ['-pk']
    name = models.CharField(max_length=100)
    time = models.DateTimeField('Time', auto_now_add=True)
    type_choices = ['testing', 'calibration', 'validation', 'prediction']
    type = models.CharField('Type', max_length=32, default='testing',
                            choices=zip(type_choices, type_choices))
    notes = models.TextField('Notes', blank=True)
