import subprocess
import json

from django.core.management.base import BaseCommand, CommandError

from parsing_scripts import git_update
from ports.models import Port, Commit

RSYNC = "rsync://rsync.macports.org/macports//trunk/dports/PortIndex_darwin_16_i386/PortIndex.json"
JSON_FILE = "portindex.json"


class Command(BaseCommand):
    help = "Populates the database with Initial data from portindex.json file"

    def add_arguments(self, parser):
        parser.add_argument('new',
                            nargs='?',
                            default=False,
                            help="Define a commit till which the update should be processed")
        parser.add_argument('old',
                            nargs='?',
                            default=False,
                            help="Not recommended. Helps you provide a commit from which update should start")

    def handle(self, *args, **options):
        ports_to_be_updated = git_update.get_list_of_changed_ports(options['new'], options['old'])

        # fetch from rsync
        subprocess.call(['rsync', RSYNC, JSON_FILE])

        # Run updates
        Port.update(ports_to_be_updated, is_json=False)

        # Open the file
        with open(JSON_FILE, "r") as file:
            data = json.load(file)

        # Write commit hash to database
        if options['new'] is False:
            Commit.objects.create(hash=data['info']['commit'])
        else:
            Commit.objects.create(hash=options['new'])
