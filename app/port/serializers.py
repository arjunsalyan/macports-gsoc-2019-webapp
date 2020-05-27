from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from maintainer.serializers import MaintainerSerializer
from variant.serializers import VariantSerializer
from port.models import Port
from port.search_indexes import PortIndex
from maintainer.search_indexes import MaintainerIndex


# Used by autocomplete search queries
class PortHaystackSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()


class PortSerializer(serializers.ModelSerializer):
    maintainers = MaintainerSerializer(read_only=True, many=True)
    variants = VariantSerializer(read_only=True, many=True)

    class Meta:
        model = Port
        fields = ('name',
                  'portdir',
                  'categories',
                  'maintainers',
                  'version',
                  'variants',
                  'license',
                  'platforms',
                  'epoch',
                  'replaced_by',
                  'homepage',
                  'description',
                  'long_description',
                  'active')


class SearchSerializer(HaystackSerializer):
    serialize_objects = False
    maintainers = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        index_classes = [PortIndex, MaintainerIndex]

        fields = [
            'name',
            'version',
            'description',
            'categories',
            'livecheck_outdated',
            'livecheck_broken',
            'active'
        ]

    def get_maintainers(self, obj):
        return obj.maintainers

    def get_variants(self, obj):
        return obj.variants