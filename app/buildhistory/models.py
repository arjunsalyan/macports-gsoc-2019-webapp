import urllib.request
import ssl
import json
import datetime

from django.db import models, transaction

from config import BUILDERS_JSON_URL, BUILDBOT_URL_PREFIX, BUILDS_FETCHED_COUNT


class Builder(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name="Name of the builder as per Buildbot")
    display_name = models.CharField(max_length=20, db_index=True, default='', verbose_name="Simplified builder name: 10.XX")
    natural_name = models.CharField(max_length=50, default='', verbose_name="Name of the MacOS version, e.g. Catalina")

    def __str__(self):
        return "%s" % self.name

    class Meta:
        db_table = "builder"
        verbose_name = "Builder"
        verbose_name_plural = "Builders"


class BuildHistory(models.Model):
    builder_name = models.ForeignKey(Builder, on_delete=models.CASCADE, related_name='builds')
    build_id = models.IntegerField()
    status = models.CharField(max_length=50)
    port_name = models.CharField(max_length=100)
    time_start = models.DateTimeField()
    time_elapsed = models.DurationField(null=True)
    watcher_id = models.IntegerField()

    class Meta:
        db_table = "builds"
        verbose_name = "Build"
        verbose_name_plural = "Builds"
        indexes = [
            models.Index(fields=['port_name', 'builder_name', '-build_id']),
            models.Index(fields=['port_name', 'builder_name', '-time_start']),
            models.Index(fields=['port_name', 'status', 'builder_name']),
            models.Index(fields=['port_name', 'builder_name']),
            models.Index(fields=['port_name', 'status']),
            models.Index(fields=['-time_start']),
            models.Index(fields=['port_name']),
            models.Index(fields=['status']),
            models.Index(fields=['builder_name'])
        ]

    @classmethod
    def populate(cls):
        url_prefix = BUILDBOT_URL_PREFIX

        def get_url_json(builder_name, build_number):
            return '{}/json/builders/ports-{}-builder/builds/{}'.format(url_prefix, builder_name, build_number)

        def get_url_build(builder_name, build_number):
            return '{}/builders/ports-{}-builder/builds/{}'.format(url_prefix, builder_name, build_number)

        def get_files_url(builder_name, build_number):
            return '{}/builders/ports-{}-builder/builds/{}/steps/install-port/logs/files/text'.format(url_prefix, builder_name, build_number)

        def get_data_from_url(url):
            gcontext = ssl.SSLContext()
            try:
                with urllib.request.urlopen(url, context=gcontext) as u:
                    data = json.loads(u.read().decode())
                return data
            except urllib.error.URLError:
                return {}

        def get_text_from_url(url):
            gcontext = ssl.SSLContext()
            try:
                lines = urllib.request.urlopen(url, context=gcontext)
                return lines
            except urllib.error.URLError:
                return []

        def get_build_properties(array):
            properties = {}
            for prop in array['properties']:
                properties[prop[0]] = prop[1]
            return properties

        def return_summary(builder_name, build_number, build_data):
            data = {}

            properties = get_build_properties(build_data)
            port_name = properties['portname']
            status = ' '.join(build_data['text'])
            time_start = build_data['times'][0]
            time_build = float(build_data['times'][1]) - float(build_data['times'][0])

            data['name'] = port_name
            data['url'] = get_url_build(builder_name, build_number)
            data['watcher_id'] = properties['triggered_by'].split('/')[6]
            data['watcher_url'] = properties['triggered_by']
            data['status'] = status
            data['builder'] = builder_name
            data['buildnr'] = build_number
            data['time_start'] = str(datetime.datetime.fromtimestamp(int(float(time_start)), tz=datetime.timezone.utc))
            data['buildtime'] = str(
                datetime.timedelta(seconds=int(float(time_build)))) if time_build != -1 else None

            return data

        def load_build_to_db(builder_obj, data):
            build = BuildHistory()
            build.port_name = data['name']
            build.status = data['status']
            build.build_id = data['buildnr']
            build.time_start = data['time_start']
            build.time_elapsed = data['buildtime']
            build.builder_name = builder_obj
            build.build_url = data['url']
            build.watcher_url = data['watcher_url']
            build.watcher_id = data['watcher_id']
            build.save()
            return build

        @transaction.atomic()
        def load_files_to_db(build_obj, lines):
            for line in lines:
                decoded_line = line.decode("utf-8")
                file_obj = InstalledFile()
                file_obj.build = build_obj
                file_obj.file = decoded_line
                file_obj.save()

        for builder in Builder.objects.all():
            buildername = builder.name
            # fetch the last build first in order to figure out its number
            last_build_data = get_data_from_url(get_url_json(builder.name, -1))
            if not last_build_data:
                continue
            last_build_number = last_build_data['number']
            last_build_in_db = BuildHistory.objects.filter(builder_name_id=builder.id).order_by('-build_id').first()
            if last_build_in_db:
                build_in_database = last_build_in_db.build_id + 1
            else:
                build_in_database = last_build_number - BUILDS_FETCHED_COUNT

            for build_number in range(build_in_database, last_build_number):
                build_data = get_data_from_url(get_url_json(buildername, build_number))
                installed_files = get_text_from_url(get_files_url(buildername, build_number))
                if not build_data:
                    break
                build_data_summary = return_summary(buildername, build_number, build_data)
                build_obj = load_build_to_db(builder, build_data_summary)
                load_files_to_db(build_obj, installed_files)

    @classmethod
    def populate_builders(cls):
        gcontext = ssl.SSLContext()
        with urllib.request.urlopen(BUILDERS_JSON_URL, context=gcontext) as u:
            data = json.loads(u.read().decode())

        builders = []
        for key in data:
            if not key.split('-')[0] == 'ports':
                continue

            if not key.split('-')[2] == 'builder':
                continue

            if not len(data[key]['cachedBuilds']) > 0:
                continue

            builders.append(Builder(name=key.split('-')[1]))
        Builder.objects.bulk_create(builders)


class InstalledFile(models.Model):
    build = models.ForeignKey('buildhistory.BuildHistory', on_delete=models.CASCADE, related_name='files')
    file = models.TextField()

    class Meta:
        db_table = "installed_files"
        verbose_name = "File"
        verbose_name_plural = "Files"
