from django.test import TestCase, Client
from django.urls import reverse
from ports.models import Maintainer, Port
from parsing_scripts import load_initial_data, update


class TestMaintainers(TestCase):
    def setUp(self):
        ports = load_initial_data.open_portindex_json("ports/tests/sample_data/portindex.json")
        load_initial_data.load_categories_table(ports)
        load_initial_data.load_ports_and_maintainers_table(ports)

    def test_unique_entries_created(self):
        self.assertEquals(Maintainer.objects.count(), 6, "Failed to create unique entities for maintainers")

    def test_fetch_using_github(self):
        client = Client()
        response = client.get(reverse('maintainer_detail_github', kwargs={'github_handle': 'user'}))
        maintainers_returned = response.context['maintainers']
        num_of_ports = response.context['all_ports_num']
        self.assertEquals(maintainers_returned.count(), 3)
        self.assertEquals(num_of_ports, 4)

    def test_fetch_using_email(self):
        client = Client()
        response = client.get(reverse('maintainer_detail_email', kwargs={'name': 'user', 'domain': 'email.com'}))
        maintainers_returned = response.context['maintainers']
        num_of_ports = response.context['all_ports_num']
        self.assertEquals(maintainers_returned.count(), 3)
        self.assertEquals(num_of_ports, 3)

    def test_maintainers_updated(self):
        updated_port = [{
            "name": "port-A1",
            "portdir": "categoryA/port-A1",
            "version": "1.0.0",
            "maintainers": [
                {
                    "email": {
                        "domain": "email.com",
                        "name": "new_user"
                    },
                    "github": "new_user"
                },
                {
                    "github": "user"
                }
            ]
        }]
        update.full_update_ports(updated_port)
        port = Port.objects.get(name="port-A1")
        self.assertEquals(port.maintainers.count(), 2)
        self.assertEquals(Maintainer.objects.all().count(), 7)
        self.assertEquals(Port.objects.get(name="port-A3").maintainers.count(), 1)
