# Generated by Django 5.1.1 on 2024-10-30 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_followrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='profile_completed',
            field=models.BooleanField(default=False),
        ),
    ]