# Generated by Django 2.2.10 on 2020-06-05 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildhistory', '0003_auto_20200528_1021'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['port_name', 'status'], name='builds_port_na_8769b9_idx'),
        ),
    ]
