# Generated by Django 5.0.6 on 2024-08-09 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AI', '0006_threads_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='threads',
            name='purpose',
            field=models.CharField(default='默认/全屋管家', max_length=50),
            preserve_default=False,
        ),
    ]
