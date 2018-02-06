# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-06 13:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tags', models.CharField(blank=True, max_length=1024)),
                ('name', models.CharField(max_length=128)),
                ('value', models.DecimalField(decimal_places=8, max_digits=16)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResultFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tags', models.CharField(blank=True, max_length=1024)),
                ('file', models.FileField(upload_to=b'results')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ResultIndicator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tags', models.CharField(blank=True, max_length=1024)),
                ('name', models.CharField(max_length=128)),
                ('value', models.DecimalField(decimal_places=8, max_digits=16)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True, verbose_name=b'Time')),
                ('tags', models.CharField(blank=True, max_length=1024)),
                ('notes', models.TextField(blank=True, verbose_name=b'Notes')),
            ],
        ),
        migrations.AddField(
            model_name='resultindicator',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='modelmanager.Run'),
        ),
        migrations.AddField(
            model_name='resultfile',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='modelmanager.Run'),
        ),
        migrations.AddField(
            model_name='parameter',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='modelmanager.Run'),
        ),
    ]
