# Generated by Django 3.1 on 2020-11-05 21:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0006_comment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='post',
            new_name='article',
        ),
    ]