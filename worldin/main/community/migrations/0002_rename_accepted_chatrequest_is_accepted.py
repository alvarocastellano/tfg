# Generated by Django 5.1.1 on 2024-12-17 12:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chatrequest',
            old_name='accepted',
            new_name='is_accepted',
        ),
    ]
