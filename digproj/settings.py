"""
Django settings for digproj project.

Generated by 'django-admin startproject' using Django 2.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from decouple import config
from dj_database_url import parse as dburl

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


ALLOWED_HOSTS = [
    '52.44.41.170', #AWS Elastic IP 26-12-24 for instance digproj1224
    '44.198.138.125', #AWS Elastic IP 22-3-24 for instance digproj
    'digest.com.br',
    'localhost',
    '127.0.0.1',
]

#evironment vars done (DEBUG, SECRET_KEY, DB, EMAIL) with decouple.config
#stored at .env (must go to .gitignore)
#DEBUG = True
############## For local DB, localhost ###########
#SECRET_KEY='h%$7j91w!qrkc=ve+0g#^vz)x=n-9@-b70fs@6a*fb$m9^4mxx'
##################################################
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'core',
    'django_filters',
#   'storages',
    'user',
    'persona',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'digproj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DEFAULT_AUTO_FIELD='django.db.models.AutoField' 

WSGI_APPLICATION = 'digproj.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_URL').split('/')[-1],
        'USER': config('DATABASE_URL').split('//')[1].split(':')[0],
        'PASSWORD': config('DATABASE_URL').split(':')[2].split('@')[0],
        'HOST': config('DATABASE_URL').split('@')[1].split(':')[0],
        'PORT': config('DATABASE_URL').split(':')[-1].split('/')[0],
    }
}

############## For local DB, localhost ###########
DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql',
         'NAME': 'dig',
         'USER': '',
         'PASSWORD': '',
         'HOST': 'localhost',
         'PORT': '5432',
     }
}
##################################################

#SECURE_REFERRER_POLICY = "no-referrer-when-downgrade"

CORS_ORIGIN_ALLOW_ALL = True

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Fortaleza'

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

AUTH_USER_MODEL = 'core.User'

EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

EMAIL_HOST_USER = 'miguel.sza@gmail.com'
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Compress static files for serving
# https://warehouse.python.org/project/whitenoise
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

#AWS_ACCESS_KEY_ID = config('your-access-key-id')
#AWS_SECRET_ACCESS_KEY = config('your-secret-access-key')
#AWS_STORAGE_BUCKET_NAME = config('your-bucket-name')
#AWS_S3_REGION_NAME = config('your-region')  # e.g., 'us-east-1'

"""Added 22-12-25"""

#SECURE_SSL_REDIRECT = True
#SESSION_COOKIE_SECURE = True
#CSRF_COOKIE_SECURE = True


