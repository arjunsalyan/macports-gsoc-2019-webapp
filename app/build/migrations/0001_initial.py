# Generated by Django 2.2.10 on 2020-04-23 18:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Builder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, verbose_name='Name of the builder as per Buildbot')),
                ('display_name', models.CharField(db_index=True, default='', max_length=20, verbose_name='Simplified builder name: 10.XX')),
            ],
            options={
                'verbose_name': 'Builder',
                'verbose_name_plural': 'Builders',
                'db_table': 'builder',
            },
        ),
        migrations.CreateModel(
            name='BuildHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('build_id', models.IntegerField()),
                ('status', models.CharField(max_length=50)),
                ('port_name', models.CharField(max_length=100)),
                ('time_start', models.DateTimeField()),
                ('time_elapsed', models.DurationField(null=True)),
                ('watcher_id', models.IntegerField()),
                ('builder_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='build.Builder')),
            ],
            options={
                'verbose_name': 'Build',
                'verbose_name_plural': 'Builds',
                'db_table': 'builds',
            },
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['port_name', 'builder_name', '-build_id'], name='builds_port_na_690929_idx'),
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['port_name', 'builder_name', '-time_start'], name='builds_port_na_a30f18_idx'),
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['port_name', 'status', 'builder_name'], name='builds_port_na_a1a05a_idx'),
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['port_name', 'builder_name'], name='builds_port_na_9b04f4_idx'),
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['-time_start'], name='builds_time_st_741e8b_idx'),
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['port_name'], name='builds_port_na_f9cad8_idx'),
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['status'], name='builds_status_e27daf_idx'),
        ),
        migrations.AddIndex(
            model_name='buildhistory',
            index=models.Index(fields=['builder_name'], name='builds_builder_5931b0_idx'),
        ),
    ]
