import uuid
from time import gmtime, strftime
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,\
                                    PermissionsMixin
from django.conf import settings
from django.utils import timezone


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a new user"""
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    # Only email and passwd! No 'name'
    def create_superuser(self, email, password):
        """Creates and saves a new superuser"""
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using email instead of username"""
    # User (7)
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    # Added is_limited, is_partner, is_staff
    is_active = models.BooleanField(default=True)
    is_limited = models.BooleanField(default=False)
    is_partner = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    # Added after above adding
    def __str__(self):
        return self.name
    
    # Added after above adding
    class Meta:
        ordering = ['name']

class Kollege(models.Model):
    """Equipe to be used for a Persona"""
    # Kollege (4)
    name = models.CharField(max_length=255, unique=True)
    #Instead of referencing User directly, set the 1st arg (model) by settings
    # user = models.ForeignKey(
    #    settings.AUTH_USER_MODEL,
    #    on_delete=models.CASCADE
    # )
    crm = models.CharField(null=True, max_length=15, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    agenda = models.TextField(null=True, blank=True)
    genericChar = models.CharField(null=True, max_length=255, blank=True)


    def __str__(self):
        return self.name
    
    class Meta:
        # unique_together = (('name', 'crm'),)
        ordering = ['name']
        index_together = (('name', 'crm'),)

class Partner(models.Model):
    """Doctor or Clinics the persona comes from"""
    # Partner (6)
    name = models.CharField(max_length=255, unique=True)
    crm = models.CharField(null=True, max_length=15, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    whatsapp = models.CharField(null=True, max_length=20, blank=True)
    telephone = models.CharField(null=True, max_length=20, blank=True)
    genericChar = models.CharField(null=True, max_length=255, blank=True)


    def __str__(self):
        return self.name
    
    class Meta:
        # unique_together = (('name', 'crm'),)
        ordering = ['name']
        index_together = (('name', 'crm'),)

class Procedure(models.Model):
    """Procedures and values delivered"""
    # Partner (6)
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(null=True, max_length=15, blank=True, unique=True)
    value1 = models.CharField(null=True, max_length=15, blank=True)
    value2 = models.CharField(null=True, max_length=15, blank=True)
    value3 = models.CharField(null=True, max_length=25, blank=True)
    genericChar = models.CharField(null=True, max_length=255, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = (('name', 'code'),)
        ordering = ['name']
        index_together = (('name', 'code'),)


class Event(models.Model):
    """Event to occur to a persona = 19 fields + ID"""
    # pylint: disable=no-member
    # user = models.ForeignKey(
    #    settings.AUTH_USER_MODEL,
    #    on_delete=models.CASCADE
    # )

    # Event (19)
    title = models.CharField(max_length=100)
    partner = models.CharField(null=True, max_length=255, blank=True)
    start = models.DateTimeField(blank=True)
    color = models.CharField(null=True, max_length=20, blank=True)
    status = models.CharField(null=True, max_length=20, blank=True)
    insurance = models.CharField(null=True, max_length=100, blank=True)
    resourceId = models.CharField(null=True, max_length=255, blank=True)
    addtitle1 = models.CharField(null=True, max_length=100, blank=True)
    addtitle2 = models.CharField(null=True, max_length=100, blank=True)
    addtitle3 = models.CharField(null=True, max_length=100, blank=True)
    comment = models.CharField(null=True, max_length=255, blank=True)
    genericChar1 = models.CharField(null=True, max_length=255, blank=True)
    genericChar2 = models.CharField(null=True, max_length=255, blank=True)
    genericChar3 = models.CharField(null=True, max_length=255, blank=True)
    genericTime1 = models.DateTimeField(null=True, blank=True)
    genericNumber1 = models.FloatField(null=True, blank=True)
    genericNumber2 = models.FloatField(null=True, blank=True)
    genericNumber3 = models.FloatField(null=True, blank=True)
    genericText = models.TextField(null=True, blank=True)


    persona = models.ForeignKey('Persona',
                                on_delete=models.CASCADE,
                                related_name='events-persona+')
    kollege = models.ForeignKey('Kollege',
                                 on_delete=models.CASCADE)
    # This onr to one permits multiple eventReports per event
    #eventReport = models.OneToOneField('EventReport', on_delete=models.CASCADE)
    #eventreport = models.ForeignKey('EventReport',
     #                               on_delete=models.CASCADE)

    def __str__(self):
        name = self.start.strftime('%x'+' %X') + ' ' + self.title
        return name

    class Meta:
        ordering = ['start']

class EventReport(models.Model):
    """Report of each event of EGD, colo, mano, pH, or else"""
    # EventReport (33)
    #event = models.OneToOneField('Event', on_delete=models.CASCADE)
    #reportUUID = models.UUIDField(default=uuid.uuid4, editable=False)

    # https://www.geeksforgeeks.org/imagefield-django-models/
    '''def event_directory_path(self, event, filename):
        # file will be uploaded to MEDIA_ROOT / user_<id>/<filename>
        filename = 0
        for i in range(10):
            name = 'persona_{0}/{1}/{2}'.format(event.persona, event.id, i)
            filename += 1
            return name
    ''' 
    def pictime(self, arg1 = 'x', arg2 = 'event'):
        # arg1 recieves the original picture name. Must give a picture name during capture
        # arg2 intended to recieve event
        time = strftime('%Y/%m/%d/')
        picurl =  time + arg2 + '/' + arg1
        return picurl
    
    # Images (10)
    # https://www.geeksforgeeks.org/imagefield-django-models/
    #im1 = models.ImageField(upload_to ='uploads/% Y/% m/% d/')
    '''im1 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im2 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im3 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im4 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im5 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im6 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im7 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im8 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im9 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)
    im10 = models.ImageField(upload_to = event_directory_path, null=True, blank=True)'''

    #im1 = models.ImageField(upload_to = pictime, blank=True)
    #id = models.IntegerField(null=False, blank=False)
    im1 =  models.TextField(null=True, blank=True)
    im2 = models.TextField(null=True, blank=True)
    im3 = models.TextField(null=True, blank=True)
    im4 = models.TextField(null=True, blank=True)
    im5 = models.TextField(null=True, blank=True)
    im6 = models.TextField(null=True, blank=True)
    im7 = models.TextField(null=True, blank=True)
    im8 = models.TextField(null=True, blank=True)
    im9 = models.TextField(null=True, blank=True)
    im10 = models.TextField(null=True, blank=True)

    # Laudos (23)
    #id = models.IntegerField(null=False, blank=False)
    drugs = models.CharField(null=True, max_length=255, blank=True)
    anest = models.CharField(null=True, max_length=255, blank=True)
    assistant = models.CharField(null=True, max_length=255, blank=True)
    equipment = models.CharField(null=True, max_length=255, blank=True)
    phar = models.TextField(null=True, blank=True)
    esop = models.TextField(null=True, blank=True)
    stom = models.TextField(null=True, blank=True)
    duod = models.TextField(null=True, blank=True)
    urease = models.CharField(null=True, max_length=255, blank=True)
    biopsy = models.CharField(null=True, max_length=255, blank=True)
    hystoResults = models.CharField(null=True, max_length=255, blank=True)
    prep = models.TextField(null=True, blank=True)
    quality = models.CharField(null=True, max_length=255, blank=True)
    colo = models.TextField(null=True, blank=True)
    genericDescription = models.TextField(null=True, blank=True)
    conc1 = models.CharField(null=True, max_length=255, blank=True)
    conc2 = models.CharField(null=True, max_length=255, blank=True)
    conc3 = models.CharField(null=True, max_length=255, blank=True)
    conc4 = models.CharField(null=True, max_length=255, blank=True)
    conc5 = models.CharField(null=True, max_length=255, blank=True)
    conc6 = models.CharField(null=True, max_length=255, blank=True)
    complications = models.CharField(null=True, max_length=255, blank=True)
    genericChar = models.CharField(null=True, max_length=255, blank=True)
    #event = models.OneToOneField('Event', on_delete=models.CASCADE,)
    #500 Error: no field 'id' in eventreport. Or, integrity error, occurred cause Django created an auto id as primary key.
    #The primary key must be the event.
    #Ex at https://docs.djangoproject.com/en/5.0/topics/db/examples/one_to_one/ has a primary_key !!!
    event = models.ForeignKey('Event', on_delete=models.CASCADE)

    #event = models.ForeignKey('Event', on_delete=models.CASCADE)

    # Cause of this, conc1 is required. If not, gets error: __str__ not a string
    def __str__(self):
        return str(self.conc1)+" "+str(self.conc2)

    class Meta:
        ordering = ['id', 'assistant',]


class Persona(models.Model):
    """Persona model"""
    # Persona (11)
    # user = models.ForeignKey(
    #    settings.AUTH_USER_MODEL,
    #    on_delete=models.CASCADE
    # )
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=20)
    whatsapp = models.CharField(null=True, max_length=20, blank=True)
    telephone = models.CharField(null=True, max_length=20, blank=True)
    email = models.EmailField(null=True, blank=True)
    street = models.CharField(null=True, max_length=255, blank=True)
    complement = models.CharField(null=True, max_length=100, blank=True)
    postalcode = models.CharField(null=True, max_length=20, blank=True)
    dob = models.DateField(null=True, blank=True)
    registerdate = models.DateTimeField(null=True)
    #registerdate = models.DateTimeField(null=True, default=timezone.now)
    comment = models.CharField(null=True, max_length=255, blank=True)
    #kollegen = models.ManyToManyField('Kollege')
    #events = models.ManyToManyField('Event')

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'dob'),)
        index_together = (('name', 'dob'),)

    def __str__(self):
        return self.name

class GenericGroup(models.Model):
    """Fields for extra data, i.e., gg1 for log"""
    #GenericGroup (10)
    gg1 = models.CharField(null=True, max_length=255, blank=True)
    gg2 = models.CharField(null=True, max_length=255, blank=True)
    gg3 = models.CharField(null=True, max_length=255, blank=True)
    gg4 = models.CharField(null=True, max_length=255, blank=True)
    gg5 = models.FloatField(null=True, blank=True)
    gg6 = models.FloatField(null=True, blank=True)
    gg7 = models.FloatField(null=True, blank=True)
    gg8 = models.TextField(null=True, blank=True)
    gg9 = models.BooleanField(null=True, blank=True)
    gg10 = models.TextField(null=True, max_length=255, blank=True)

    class Meta:
        ordering = ['gg1']

    def __str__(self):
        # To garanttee a string. App may post a null property to gg1
        # (non-string) which would cause an error in the admin site
        return str(self.gg1) + str(self.id)

class EmailFromSite(models.Model):
    """Email from the home page"""
    # EmailFromSite (4)
    name = models.CharField(null=True, max_length=255, blank=True)
    mobile = models.CharField(null=True, max_length=255, blank=True)
    email = models.CharField(null=True, max_length=255, blank=True)
    body = models.CharField(null=True, max_length=255, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name