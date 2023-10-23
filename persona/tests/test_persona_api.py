from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Persona, Kollege, Event

from persona.serializers import PersonaSerializer, PersonaDetailSerializer


PERSONA_URL = reverse('persona:persona-list')


# For the detail URL, we need arg in a function to pass to a url
def detail_url(persona_id):
    """Return persona detail url"""
    # The name of th endpoint the default router will create for the viewset:
    # gone have a detail action
    return reverse('persona:persona-detail', args=[persona_id])


def sample_kollege(user, name='Miguel', crm='222'):
    """Create and return a sample tag"""
    return Kollege.objects.create(user=user, name=name, crm=crm)


def sample_event(user, title='Colono', start='2020-12-30 07:45:00.0000'):
    """ Create and return a sample event"""
    return Event.objects.create(user=user, title=title, start=start)


# ** means that any additional args other than user will be passed as a dict
# called params
def sample_persona(user, **params):
    """Create and return a sample persona"""
    defaults = {
        'name': 'Miguel',
        'mobile': '5585999568827'
    }
    defaults.update(params)

    return Persona.objects.create(user=user, **defaults)


class PublicPersonaApiTests(TestCase):
    """Test unauthenticated persona api access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required"""
        res = self.client.get(PERSONA_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePersonaApiTests(TestCase):
    """Test auth persona api access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@ufc.br',
            'testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_personas(self):
        """Test retrieving a list of personas"""
        # Error: Positional args follow kw args
        # sample_recipe(user=self.user, {
        #    'title': '',
        #    'time_minutes': 10,
        #    'price': 5.00
        # })
        # sample_recipe(user=self.user, {
        #    'title': '',
        #    'time_minutes': 20,
        #    'price': 10.00
        # })
        # ##### Accepted this one. Lets see!!! #######
        # sample_recipe({
        #    'title': 'Fried fish',
        #    'time_minutes': 10,
        #    'price': 5.00
        # TypeError: sample_recipe() got multiple values for argument 'user'
        # }, user=self.user)
        sample_persona(user=self.user)
        sample_persona(user=self.user)

        res = self.client.get(PERSONA_URL)

        # If don't order_by('-id'), no error: AssertionError: [OrderedDict
        # ([('id', 4), ('title', 'Sample recipe'), ('time_mi[221 chars]])])] !=
        # [OrderedDict([('id', 5), ('title', 'Sample recipe'), ('time_mi[221
        # chars]])])]
        # recipes = Recipe.objects.all().order_by('-id')
        personas = Persona.objects.all().order_by('name')
        serializer = PersonaSerializer(personas, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_personas_limited_to_user(self):
        """Test retrieving personas for auth user only"""
        user2 = get_user_model().objects.create_user(
            'other@ufc.br',
            'pasrd'
        )
        sample_persona(user=user2)
        sample_persona(user=self.user)

        res = self.client.get(PERSONA_URL)

        personas = Persona.objects.filter(user=self.user)
        serializer = PersonaSerializer(personas, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_persona_detail(self):
        """Test viewing a persona detail with related objects"""
        persona = sample_persona(user=self.user)
        persona.kollegen.add(sample_kollege(user=self.user))
        persona.events.add(sample_event(user=self.user))

        url = detail_url(persona.id)
        res = self.client.get(url)

        serializer = PersonaDetailSerializer(persona)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_persona(self):
        """Test creating persona"""
        payload = {
            'name': 'José Silva',
            'mobile': '+5585988764321'
        }
        # The request creates a Persona object
        res = self.client.post(PERSONA_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # what if we had two personas?
        # When one creates an obj wth rest_framework, the default behavior is
        # to return a dict containing the created obj.
        persona = Persona.objects.get(id=res.data['id'])
        # Loop through the payload keys and asserts if each payload key is
        # equeal to each persona key.
        # One cannot retrieve the persona key with persona.key. Needs a func
        # that gets attr with args (getattr)
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(persona, key))

    def test_create_persona_with_kollegen(self):
        """Test creating personas with kollegen"""
        kol1 = sample_kollege(user=self.user)
        kol2 = sample_kollege(user=self.user)
        payload = {
            'name': 'José Silva',
            # List of kollegen id assigned to the persona.
            'kollegen': [kol1.id, kol2.id],
            'mobile': '+558599995678'
        }
        res = self.client.post(PERSONA_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        persona = Persona.objects.get(id=res.data['id'])
        kollegen = persona.kollegen.all()
        self.assertEqual(kollegen.count(), 2)
        self.assertIn(kol1, kollegen)
        self.assertIn(kol2, kollegen)

    def test_create_persona_with_events(self):
        """Test creating persona with events"""
        event1 = sample_event(user=self.user,
                              title='pH',
                              start='2020-04-19 08:30')
        event2 = sample_event(user=self.user,
                              title='MAR',
                              start='2020-04-19 08:30')
        payload = {
            'name': 'José Silva',
            'events': [event1.id, event2.id],
            'mobile': '5588999765646'
        }
        res = self.client.post(PERSONA_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        persona = Persona.objects.get(id=res.data['id'])
        events = persona.events.all()
        self.assertEqual(events.count(), 2)
        self.assertIn(event1, events)
        self.assertIn(event2, events)

        # Right now, that itens were no assigned to users (fixed on views):
        # IntegrityError:
        # null value in column "user_id" violates not-null constraint
        # DETAIL:  Failing row contains (4, Avocado lime cheesecake, 60, 20.00,
        # ,null).
