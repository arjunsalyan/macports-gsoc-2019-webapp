# Generated by Django 2.1.7 on 2019-05-14 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ports', '0003_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='uuid',
            field=models.CharField(db_index=True, max_length=36),
        ),
    ]
