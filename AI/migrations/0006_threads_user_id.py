# Generated by Django 5.0.6 on 2024-08-08 14:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AI', '0005_files'),
    ]

    operations = [
        migrations.AddField(
            model_name='threads',
            name='user_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='AI.users'),
        ),
    ]
