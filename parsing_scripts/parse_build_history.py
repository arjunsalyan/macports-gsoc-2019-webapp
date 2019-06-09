import os
import urllib.request
import ssl
import json
import sys
import datetime

import django
from django.utils import timezone

from ports.models import BuildHistory, Builder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'MacPorts.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MacPorts.settings")

django.setup()


builders = ['10.9_x86_64']
url_prefix = 'https://build.macports.org'


def get_url_json(builder_name, build_number):
    return '{}/json/builders/ports-{}-builder/builds/{}'.format(url_prefix, builder_name, build_number)


def get_url_build(builder_name, build_number):
    return '{}/builders/ports-{}-builder/builds/{}'.format(url_prefix, builder_name, build_number)


def get_data_from_url(url):
    gcontext = ssl.SSLContext()
    with urllib.request.urlopen(url, context=gcontext) as u:
        data = json.loads(u.read().decode())
    return data


def get_build_properties(array):
    properties = {}
    for prop in array['properties']:
        properties[prop[0]] = prop[1]
    return properties


def get_build_steps(array):
    steps = {}
    for step in array['steps']:
        steps[step['name']] = step
    return steps


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
    data['time_start'] = str(datetime.datetime.fromtimestamp(int(float(time_start)), tz=timezone.utc))
    data['buildtime'] = str(datetime.timedelta(seconds=int(float(time_build)))) if time_build is not -1 else None

    return data


def load_database(data):
    builder = Builder.objects.get(name=data['builder'])
    build = BuildHistory()
    build.port_name = data['name']
    build.status = data['status']
    build.build_id = data['buildnr']
    build.time_start = data['time_start']
    build.time_elapsed = data['buildtime']
    build.builder_name = builder
    build.build_url = data['url']
    build.watcher_url = data['watcher_url']
    build.watcher_id = data['watcher_id']
    build.save()


fulldata = {}


def add_to_summary(data):
    if not data['name'] in fulldata:
        fulldata[data['name']] = {}
    if not data['builder'] in fulldata[data['name']]:
        fulldata[data['name']][data['builder']] = []
    fulldata[data['name']][data['builder']].append(data)


def fetch():
    for buildername in builders:
        print()
        # fetch the last build first in order to figure out its number (the build itself might not be finished yet)
        last_build_data = get_data_from_url(get_url_json(buildername, -1))
        last_build_number = last_build_data['number']
        build_number_loaded = BuildHistory.objects.filter(builder_name__name=buildername).order_by('-build_id')
        if build_number_loaded:
            build_in_database = build_number_loaded[0].build_id + 1
        else:
            build_in_database = last_build_number - 9999

        # lets start with the latest four builds

        for build_number in range(build_in_database, last_build_number):
            build_data = get_data_from_url(get_url_json(buildername, build_number))
            build_data_summary = return_summary(buildername, build_number, build_data)
            add_to_summary(build_data_summary)
            load_database(build_data_summary)
