from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Event

from persona.serializers import EventSerializer

# View_set adds the action (list) to the name
EVENTS_URL = reverse('persona:event-list')


class PublicEventsApiTests(TestCase):
    """Test the publicly available events API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving events"""
        res = self.client.get(EVENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateEventsApiTests(TestCase):
    """Test the authorized user events API"""

    # May create a helper to create user
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@ufc.br',
            'testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_events_list(self):
        """Test retrieving a list of events"""
        # 1. Creates the objects
        Event.objects.create(user=self.user,
                             title='EDA',
                             start='2020-04-20 10:00')
        Event.objects.create(user=self.user,
                             title='EDA',
                             start='2020-04-20 10:00')
        # 2. Makes a request. The events are in res.
        # Data as raw data not objects.
        res = self.client.get(EVENTS_URL)
        # 3. Creates a list of all events (objects)
        events = Event.objects.all().order_by('-title')
        # 4. Serializes the tag objects. The tags are in serializer.data as raw
        serializer = EventSerializer(events, many=True)
        # 5. Makes the assertions
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_events_limited_to_user(self):
        """Test that events returned are for the authenticated users"""
        # Creates a user that shall not be authenticated
        user2 = get_user_model().objects.create_user(
            'other@ufc.br',
            'testpass'
        )
        # Creates events for the unauth and the auth users
        Event.objects.create(user=user2,
                             title='pHmetria',
                             start='2020-04-20 10:00')
        event = Event.objects.create(user=self.user,
                                     title='MAR',
                                     start='2020-04-20 10:00')

        res = self.client.get(EVENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], event.title)

    def test_create_event_successful(self):
        """Test create a new event"""
        payload = {'title': 'Colono', 'start': '2020-05-02 08:00:00.000'}
        self.client.post(EVENTS_URL, payload)

        exists = Event.objects.filter(
            user=self.user,
            title=payload['title'],
            start=payload['start']
        ).exists()

        self.assertTrue(exists)

    def test_create_event_invalid(self):
        """Test creating invalid event fails"""
        payload = {'title': '', 'start': '2020-05-02 08:00:00'}
        res = self.client.post(EVENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
