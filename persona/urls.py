# pylint: disable=import-error
# pylint: disable=no-name-in-module
from django.urls import path
from persona import views
from rest_framework.urlpatterns import format_suffix_patterns


urlpatterns =[
      path('', views.api_root),
      path('inicio/',
            views.EventList.as_view()),
      path('users/',
           views.UserList.as_view(),
           name='user-list'),
      path('users/<int:pk>/',
           views.UserDetail.as_view(),
           name='user-detail'),
      path('events/',
            views.EventList.as_view(),
            name='event-list'),
      path('events/<int:pk>/',
            views.EventDetail.as_view(),
            name='event-detail'),
      path('genericgroup/',
            views.GenericGroupList.as_view(),
            name='genericgroup-list'),
      path('genericgroup/<int:pk>',
            views.GenericGroupListDetail.as_view(),
            name='genericgroup-detail'),
      path('kollegen/',
            views.KollegeList.as_view(),
            name='kollege-list'),
      path('email/',
            views.EmailKollege.as_view(),
            name='email-kollege'),  
      path('emailserv/',
            views.EmailFromSite.as_view(),
            name='email-from-site'),  
      path('kollegen/<int:pk>/',
            views.KollegeDetail.as_view(),
            name='kollege-detail'),
      path('personas/',
            views.PersonaList.as_view(),
            name='persona-list'),
      path('personas/<int:pk>/',
            views.PersonaDetail.as_view(),
            name='persona-detail'),
      path('partners/',
            views.PartnerList.as_view(),
            name='partner-list'),
      path('partners/<int:pk>/',
            views.PartnerDetail.as_view(),
            name='partner-detail'),
      path('eventreports/',
            views.EventReportList.as_view(),
            name='eventreport-list'),
      path('eventreports/<int:pk>/',
            views.EventReportDetail.as_view(),
            name='eventreport-detail'),
]
'''
    path('personas/',
          views.PersonaList.as_view(),
          name='persona-list'),
    path('personas/<int:pk>',
          views.PersonaList.as_view(),
          name='persona-detail'),
    path('events/',
          views.EventList.as_view(),
          name='event-list'),
    path('events/<int:pk>',
          views.EventList.as_view(),
          name='event-detail'),
'''

'''
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from persona import views


# The DefaultRouter auto generates the urls for a viewset.
# One viewset may have multiple urls.
router = DefaultRouter()
router.register('kollegen', views.KollegeViewSet)
router.register('events', views.EventViewSet)
router.register('personas', views.PersonaViewSet)
# router.register('detail', views.PersonaViewSet)
# So the reverse function may find
app_name = 'persona'

urlpatterns = [
    # router.urls NOT a str
    path('', include(router.urls)),
    # path('index/', views.PersonaViewSet, )
]
'''
