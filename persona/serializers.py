# pylint: disable=import-error
from rest_framework import serializers
from core.models import Kollege, Event, Persona, EventReport, Partner, GenericGroup, EmailFromSite


class KollegeSerializer(serializers.ModelSerializer):
    """Serializer for equipe objects"""

    class Meta:
        model = Kollege
        fields = ('id', 'name', 'crm', 'email', 'mobile')
        read_only_fields = ('id',)

class PartnerSerializer(serializers.ModelSerializer):
    """Serializer for partner objects"""

    class Meta:
        model = Partner
        fields = ('id', 'name', 'crm', 'email', 'mobile', 'whatsapp', 'telephone')
        read_only_fields = ('id',)

class EventSerializer(serializers.ModelSerializer):
    """ Serializer for event objects - 20 fields"""

    class Meta:
        model = Event
        fields = ('id', 'title', 'partner', 'start', 'color', 'status', 'insurance', 'resourceId',
                  'addtitle1', 'addtitle2', 'addtitle3', 'comment', 'genericChar1',
                  'genericChar2', 'genericChar3', 'genericTime1', 'genericNumber1',
                  'genericNumber2', 'genericNumber3', 'persona', 'kollege')
        read_only_fields = ('id',)

class EventReportSerializer(serializers.ModelSerializer):
    """Serializer  for EventReport - 34 fields"""

    class Meta:
        model = EventReport
        fields = ('id', #'reportUUID',
                'im1', 'im2', 'im3', 'im4', 'im5', 'im6', 'im7', 'im8', 'im9', 'im10',
                'drugs', 'anest', 'assistant', 'equipment', 'phar', 'esop', 'stom', 'duod',
                'urease', 'biopsy', 'hystoResults', 'prep', 'quality', 'colo', 'genericDescription',
                'conc1', 'conc2', 'conc3', 'conc4', 'conc5', 'conc6', 'complications', 'event')
        read_only_fields = ('id',)


class PersonaSerializer(serializers.ModelSerializer):
    """Serializer for persona obj"""
#    events = serializers.PrimaryKeyRelatedField(
#       many=True,
#        queryset=Event.objects.all()
#   )
#   kollegen = serializers.PrimaryKeyRelatedField(
#       many=True,
#       queryset=Kollege.objects.all()
#   )

    class Meta:
        model = Persona
        fields = ('id', 'name', 'mobile', 'whatsapp', 'telephone', 'email',
                  'street', 'complement', 'postalcode', 'dob', 'registerdate',
                  'comment', #'kollegen', 'events'
                  )
        read_only_fields = ('id',)


class PersonaDetailSerializer(PersonaSerializer):
    """Serialize a persona detail"""
    # Override events and kollegen of the PersonaSerializer
    events = EventSerializer(many=True, read_only=True)
    kollegen = KollegeSerializer(many=True, read_only=True)

class GenericGroupSerializer(serializers.ModelSerializer):
    """Serialize the GenericGroup, i.e., log"""
    class Meta:
        model = GenericGroup
        fields = ('id', 'gg1', 'gg2', 'gg3', 'gg4', 'gg5', 'gg6', 'gg7', 'gg8', 'gg9', 'gg10')
        read_only_fields = ('id',)

class EmailFromSiteSerializer(serializers.ModelSerializer):
    """Serialize data from email sent by site"""
    class Meta:
        model = EmailFromSite
        fields = ('id', 'name', 'mobile', 'email', 'body')
        read_only_fields = ('id',)