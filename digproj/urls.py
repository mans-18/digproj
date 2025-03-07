"""digproj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# pylint: disable=import-error
# pylint: disable=no-name-in-module
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import include
from persona import views
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    #path('api/persona/events/', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('api/user/', include('user.urls')),
    path('api/persona/', include('persona.urls')),
]
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
    # from angular course
    path('auth/', obtain_auth_token),
    path('auth/', views.EventList.as_view(),
           name='event-list'),
]
