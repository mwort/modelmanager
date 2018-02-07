from django.db import models


class Variable(models.Model):
    name = models.CharField(max_length=64)
    value = models.CharField(max_length=1024)


class Function(models.Model):
    name = models.CharField(max_length=64)


class FunctionParameter(models.Model):
    function = models.ForeignKey(Function)
    name = models.CharField(max_length=64)
    TYPES = ['str', 'int', 'float', 'bool']
    type = models.CharField(max_length=16, choices=zip(TYPES, TYPES))
