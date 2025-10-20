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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import include
from persona import views
from rest_framework.authtoken.views import obtain_auth_token
from django.conf.urls.static import static


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

'''
Your Django application handles two different jobs:

1. Storage (Saving the file): Handled by the model and FileSystemStorage.
   · This is what MEDIA_ROOT and TEMP_MEDIA_STORAGE control.
   · They tell Django "save the uploaded file to this specific folder on the server's hard drive."
   · This is working correctly for you now.
2. Serving (Sending the file to a browser): Handled by a web server.
   · When a browser requests http://127.0.0.1:8000/media/temp_images/myimage.jpg, something needs to find that file on the disk and send it back.
   · In production, this job is handled by a dedicated web server like Nginx or Apache. They are extremely fast and efficient at this task.
   · In development, you don't have Nginx. So, you need something else to serve these files. This is what the static() function in urls.py does.

Without the `urls.py` line:

1. The browser requests .../media/temp_images/capture_123.jpg.
2. Django looks at its list of URL patterns (urlpatterns). It only finds patterns for admin/, api/, etc.
3. Django doesn't find a match for media/..., so it returns a 404 Page Not Found error. The image breaks.

With the `urls.py` line:

1. The browser requests .../media/temp_images/capture_123.jpg.
2. Django looks at its URL patterns. It finds the pattern added by static() which says "I handle URLs that start with `/media/`".
3. Django takes the part after /media/ (temp_images/capture_123.jpg), looks for it in the MEDIA_ROOT directory, finds the file, and serves it. The image loads correctly.

'''

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
