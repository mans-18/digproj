from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email='mans@ufc.br', password='testpass'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test create a new user with a email successful"""
        email = 'mans@ufc.br'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
            )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = 'mans@UFC.BR'
        user = get_user_model().objects.create_user(email, 'test123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_create_new_super_user(self):
        """Test creating a new super user"""
        user = get_user_model().objects.create_superuser(
            'mans@ufc.br',
            'Testpass123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_kollege_str(self):
        """Test the kollege string representation"""
        kollege = models.Kollege.objects.create(
            user=sample_user(),
            name='Miguel',
            crm='5521'
        )
        # On models.py/Kollege class, name is set as the kollege component
        # to convert to str. Could be name instead of kollege?
        self.assertEqual(str(kollege), kollege.name)

    def test_event_str(self):
        """Test the event str representation"""
        event = models.Event.objects.create(
            user=sample_user(),
            title='EDA',
            start='2020-04-20 10:00'
        )

        self.assertEqual(str(event), event.title)

    def test_persona_str(self):
        """Test the persona str representation"""
        persona = models.Persona.objects.create(
            user=sample_user(),
            name='Miguel',
            mobile='85999568827')
        self.assertEqual(str(persona), persona.name)
