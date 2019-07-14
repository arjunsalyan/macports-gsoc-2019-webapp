import os
import subprocess
import sys
import io
import shutil

import django

from ports.models import LastPortIndexUpdate

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'MacPorts.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MacPorts.settings")

django.setup()

REPO = "macports-ports"
REPO_URL = "https://github.com/macports/macports-ports.git"


def clone_repo():
    if os.path.isdir(REPO):
        return
    else:
        os.system("git clone %s" % REPO_URL)


def get_list_of_changed_ports(new_hash=False, old_hash=False, root=BASE_DIR):
    os.chdir(root)

    if os.path.isdir(REPO):
        print('{} directory found'.format(REPO))

        # cd into the macports-ports directory
        REPO_DIR = os.path.join(root, REPO)
        os.chdir(REPO_DIR)

        # Check if the repository is healthy.
        try:
            remote = subprocess.run(['git', 'config', '--get', 'remote.origin.url'],
                                    stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
            if remote == REPO_URL:
                print("The {} repo is healthy.".format(REPO))
            else:
                raise OSError

            # If old_hash is not provided by the user
            if old_hash is False:
                try:
                    # Try to fetch the most recent hash from database
                    old_hash_object = LastPortIndexUpdate.objects.all().first()
                    old_hash = old_hash_object.git_commit_hash
                except AttributeError:
                    # If database is empty, use the current HEAD
                    old_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE).stdout.decode(
                            'utf-8')

            # Pull from macports-ports
            subprocess.call(['git', 'pull'])

            # Get new hash if not provided
            if new_hash is False:
                new_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE).stdout.decode('utf-8')

            # Generate the range of commits to find updated paths
            range = str(old_hash).strip() + "^.." + str(new_hash).strip()

            changed_paths = subprocess.run(['git', 'diff', '--name-only', range], stdout=subprocess.PIPE).stdout.decode(
                'utf-8')
            s = io.StringIO(changed_paths)
            updated_ports = []
            for line in s:
                portname = line.split('/')[1]
                if portname not in updated_ports:
                    updated_ports.append(portname)

            os.chdir(BASE_DIR)
            return updated_ports

        except OSError:
            os.chdir(root)
            print("{} repository has some error".format(REPO))
            print("Cleaning current tree and cloning new repo.")
            shutil.rmtree(REPO)
            clone_repo()
            return get_list_of_changed_ports(new_hash, old_hash, root)
    else:
        print('{} directory not found. Cloning into'.format(REPO))
        clone_repo()
        return get_list_of_changed_ports(new_hash, old_hash, root)
