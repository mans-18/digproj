from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Kollege

from persona.serializers import KollegeSerializer


KOLLEGEN_URL = reverse('persona:kollege-list')


class PublicEquipesApiTests(TestCase):
    """test the publicly available equipes API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving kollegen"""
        res = self.client.get(KOLLEGEN_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateKollegenApiTests(TestCase):
    """Test the authorized user kollegen API"""

    # May create a helper to create user
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@ufc.br',
            'testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_kollegen(self):
        """Test retrieving kollegen"""
        # 1. Creates the objects
        Kollege.objects.create(user=self.user, name='Miguel')
        Kollege.objects.create(user=self.user, name='Digest')
        # 2. Makes a request. The kollegen are in res.
        # Data as raw data not objects.
        res = self.client.get(KOLLEGEN_URL)
        # 3. Creates a list of all kollegen (objects)
        kollegen = Kollege.objects.all().order_by('-name')
        # 4. Serializes the kollege objects. The kollegen are in serializer.
        # Data as raw
        serializer = KollegeSerializer(kollegen, many=True)
        # 5. Makes the assertions
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_kollegen_limited_to_user(self):
        """Test that kollegen returned are for the authenticated users"""
        # Creates a user that shall not be authenticated
        user2 = get_user_model().objects.create_user(
            'other@ufc.br',
            'testpass'
        )
        # Creates tags for the unauth and the auth users
        Kollege.objects.create(user=user2, name='Uni')
        kollege = Kollege.objects.create(user=self.user, name='Digest')

        res = self.client.get(KOLLEGEN_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], kollege.name)

    def test_create_kollege_successful(self):
        """Test creating a new kollege"""
        payload = {'name': 'Test kollege', 'crm': '0001'}
        self.client.post(KOLLEGEN_URL, payload)

        # Filter by the kollege (auth user and name)
        exists = Kollege.objects.filter(
            # May dismiss user?
            user=self.user,
            name=payload['name'],
            crm=payload['crm']
        ).exists()
        self.assertTrue(exists)

    def test_create_kollege_invalid(self):
        """Create kollege with an invalid payload"""
        payload = {'name': ''}
        res = self.client.post(KOLLEGEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
