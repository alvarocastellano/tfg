# Generated by Django 5.1.1 on 2024-12-19 09:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0006_chat_initial_message'),
        ('market', '0002_alter_rental_city_associated'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='market.product'),
        ),
    ]
