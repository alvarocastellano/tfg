# Generated by Django 5.1.1 on 2024-12-18 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_rename_accepted_chatrequest_is_accepted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chatrequest',
            name='is_accepted',
        ),
        migrations.AddField(
            model_name='chatrequest',
            name='status',
            field=models.CharField(choices=[('pending', 'Pendiente'), ('accepted', 'Aceptada'), ('rejected', 'Rechazada')], default='pending', max_length=10),
        ),
    ]
