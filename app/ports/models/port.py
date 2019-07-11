import json
import os

from django.db import models


class Category(models.Model):
    name = models.TextField(primary_key=True)


class PortManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Port(models.Model):
    portdir = models.CharField(max_length=100)
    description = models.TextField(default='')
    homepage = models.URLField(default='')
    epoch = models.BigIntegerField(default=0)
    platforms = models.TextField(null=True)
    categories = models.ManyToManyField(Category, related_name='category', db_index=True)
    long_description = models.TextField(default='')
    version = models.CharField(max_length=100, default='')
    revision = models.IntegerField(default=0)
    closedmaintainer = models.BooleanField(default=False)
    name = models.CharField(max_length=100, db_index=True)
    license = models.CharField(max_length=100, default='')
    replaced_by = models.CharField(max_length=100, null=True)

    objects = PortManager()

    @classmethod
    def load(cls, data):
        def open_portindex_json(path):
            with open(path, "r") as file:
                ports = json.load(file)
            return ports['ports']

        # Add All the Categories to the Database using bulk_create
        def load_categories_table(ports):
            categories = set()
            for port in ports:
                try:
                    for category in port['categories']:
                        categories.add(Category(name=category))
                except KeyError:
                    pass
            batch = list(categories)
            Category.objects.bulk_create(batch)
            return

        def load_ports_and_maintainers_table(ports):
            for port in ports:

                # Add Ports to the Database One-by-One
                new_port = Port()
                try:
                    new_port.name = port['name']
                    new_port.portdir = port['portdir']
                    new_port.version = port['version']
                except KeyError:
                    continue

                new_port.description = port.get('description', '')
                new_port.homepage = port.get('homepage', '')
                new_port.epoch = port.get('epoch', 0)
                new_port.platforms = port.get('platforms')
                new_port.long_description = port.get('long_description', '')
                new_port.revision = port.get('revision', 0)
                new_port.closedmaintainer = port.get('closedmaintainer', False)
                new_port.license = port.get('license', '')
                new_port.replaced_by = port.get('replaced_by')
                new_port.save()

                try:
                    new_port.categories.add(*port['categories'])
                except KeyError:
                    pass

                try:
                    for maintainer in port['maintainers']:
                        name = maintainer.get('email', {}).get('name', '')
                        domain = maintainer.get('email', {}).get('domain', '')
                        github = maintainer.get('github', '')

                        maintainer_object, created = Maintainer.objects.get_or_create(
                            name=name,
                            domain=domain,
                            github=github
                        )

                        maintainer_object.ports.add(new_port)
                except KeyError:
                    pass

                try:
                    for variant in port['variants']:
                        variant_object = Variant()
                        variant_object.port = new_port
                        variant_object.variant = variant
                        variant_object.save()
                except KeyError:
                    pass

        def load_dependencies_table(ports):

            def load_depends(list_of_dependencies, type_of_dependency, port):
                dependency = Dependency()
                dependencies = []
                dependency.type = type_of_dependency
                dependency.port_name = port
                for depends in list_of_dependencies:
                    try:
                        dependencies.append(Port.objects.get(name__iexact=depends.rsplit(':', 1)[-1]))
                    except Port.DoesNotExist:
                        print("Failed to append {} as a dependency to {}. Not Found.".format(depends.rsplit(':', 1)[-1],
                                                                                             port.name))
                dependency.save()
                dependency.dependencies.add(*dependencies)

            for port in ports:
                try:
                    port_object = Port.objects.get(name__iexact=port['name'])
                    for dependency_type in ["lib", "extract", "run", "patch", "build", "test", "fetch"]:
                        key = "depends_" + dependency_type
                        if key in port:
                            load_depends(port[key], dependency_type, port_object)

                except Port.DoesNotExist:
                    print("Failed to update dependencies for {}. Port not found in database.".format(port['name']))

        def populate(ports):
            load_categories_table(ports)
            load_ports_and_maintainers_table(ports)
            load_dependencies_table(ports)

        # If list of JSON objects in passed, start populating
        if isinstance(data, list):
            populate(data)
        # If a path to JSON file is provided, open the file and then start populating
        elif isinstance(data, str):
            ports = open_portindex_json(data)
            populate(ports)

    @classmethod
    def update(cls, data, is_json=True):
        def open_portindex_json(path):
            with open(path, "r") as file:
                ports = json.load(file)
            return ports['ports']

        def open_ports_from_list(list_of_ports, path='portindex.json'):
            with open(path, "r") as file:
                all_ports = json.load(file)
            ports_to_be_updated = []
            for port in data['ports']:
                if port['name'] in list_of_ports:
                    ports_to_be_updated.append(port)
            return ports_to_be_updated

        def full_update_ports(ports):

            for port in ports:
                port_object, port_created = Port.objects.get_or_create(name=port['name'])

                port_object.portdir = port['portdir']
                port_object.version = port['version']
                port_object.description = port.get('description', '')
                port_object.homepage = port.get('homepage', '')
                port_object.epoch = port.get('epoch', 0)
                port_object.platforms = port.get('platforms', '')
                port_object.long_description = port.get('long_description', '')
                port_object.revision = port.get('revision', 0)
                port_object.closedmaintainer = port.get('closedmaintainer', False)
                port_object.license = port.get('license', '')
                port_object.replaced_by = port.get('replaced_by')
                port_object.save()

                try:
                    port_object.categories.clear()
                    for category in port['categories']:
                        category_object, category_created = Category.objects.get_or_create(name=category)
                        port_object.categories.add(category_object)
                except KeyError:
                    pass

                try:
                    variant_objects = Variant.objects.filter(port_id=port_object.id)

                    for variant_object in variant_objects:
                        if variant_object not in port['variants']:
                            variant_object.delete()

                    for variant in port['variants']:
                        v_obj, created = Variant.objects.get_or_create(port_id=port_object.id, variant=variant)
                except KeyError:
                    pass

                try:
                    port_object.maintainers.clear()
                    for maintainer in port['maintainers']:
                        name = maintainer.get('email', {}).get('name', '')
                        domain = maintainer.get('email', {}).get('domain', '')
                        github = maintainer.get('github', '')

                        maintainer_object, created = Maintainer.objects.get_or_create(
                            name=name,
                            domain=domain,
                            github=github
                        )

                        maintainer_object.ports.add(port_object)
                except KeyError:
                    pass

        def full_update_dependencies(ports):

            for port in ports:
                try:
                    all_dependency_objects = Dependency.objects.filter(port_name__name__iexact=port['name'])
                    port_object = Port.objects.get(name=port['name'])

                    # Delete the dependency types from database that no longer exist in
                    for dependency_object in all_dependency_objects:
                        key = "depends_" + dependency_object.type
                        if key not in port:
                            dependency_object.delete()

                    for dependency_type in ["lib", "extract", "run", "patch", "build", "test", "fetch"]:
                        key = "depends_" + dependency_type
                        if key in port:
                            obj, created = Dependency.objects.get_or_create(port_name_id=port_object.id,
                                                                            type=dependency_type)
                            obj.type = dependency_type
                            obj.port_name = port_object
                            obj.dependencies.clear()
                            dependencies = []

                            for depends in port[key]:
                                try:
                                    dependencies.append(Port.objects.get(name__iexact=depends.rsplit(':', 1)[-1]))
                                except Port.DoesNotExist:
                                    print("Failed to append {} as a dependency to {}. Not Found.".format(
                                        depends.rsplit(':', 1)[-1],
                                        port.name))
                            obj.save()
                            obj.dependencies.add(*dependencies)

                except Port.DoesNotExist:
                    print(
                        "Failed to update depencies for {}. Port does not exist in the database.".format(port['name']))

        # Takes in a list of JSON objects and runs the updates
        def run_updates(ports):
            full_update_ports(ports)
            full_update_dependencies(ports)

        # Block to find type of passed "data" and run updates accordingly
        # ============ START ============

        # If the passed object is a valid path, open it and parse the JSON objects
        if isinstance(data, str):
            if os.path.exists(data):
                ports = open_portindex_json(data)
                run_updates(ports)
            else:
                print('File "{}" not found.'.format(data))

        # If the passed object is a list
        elif isinstance(data, list):
            # If the passed list contains JSON objects, run the updates directly
            if is_json:
                run_updates(data)
            # If the passed list contains names of ports, first fetch corresponding JSON objects then run the updates
            else:
                ports = open_ports_from_list(data)
                run_updates(ports)

        # ============ END ==============


class Dependency(models.Model):
    port_name = models.ForeignKey(Port, on_delete=models.CASCADE, related_name="dependent_port")
    dependencies = models.ManyToManyField(Port)
    type = models.CharField(max_length=100)

    class Meta:
        unique_together = [['port_name', 'type']]

        indexes = [
            models.Index(fields=['port_name'])
        ]


class Variant(models.Model):
    port = models.ForeignKey(Port, on_delete=models.CASCADE, related_name='ports')
    variant = models.CharField(max_length=100, default='')


class Maintainer(models.Model):
    name = models.CharField(max_length=50, default='')
    domain = models.CharField(max_length=50, default='')
    github = models.CharField(max_length=50, default='')
    ports = models.ManyToManyField(Port, related_name='maintainers')

    objects = PortManager()

    class Meta:
        unique_together = [['name', 'domain', 'github']]

        indexes = [
            models.Index(fields=['github']),
            models.Index(fields=['name', 'domain'])
        ]


class Commit(models.Model):
    hash = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)
