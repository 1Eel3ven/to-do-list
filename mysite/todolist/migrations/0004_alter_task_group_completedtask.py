# Generated by Django 5.0.2 on 2024-04-16 10:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todolist', '0003_alter_task_owner_alter_taskgroup_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='group',
            field=models.ManyToManyField(blank=True, to='todolist.taskgroup'),
        ),
        migrations.CreateModel(
            name='CompletedTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('complete_date', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)ss', related_query_name='%(app_label)s_%(class)s', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
