# pylint: disable=import-error
# pylint: disable=no-name-in-module
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from persona import views
from rest_framework.urlpatterns import format_suffix_patterns

from persona.utils.report_pdf import build_pdf_for_eventreport


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
######### 10-1-25 #########################
      path('events-limited/',
            views.EventListLimited.as_view(),
            name='event-list-limited'),
      path('personas-limited/',
            views.PersonaListLimited.as_view(),
            name='persona-list-limited'),
      path('eventsByDateRange/',
           views.EventsByDateRange.as_view(),
           name='events-by-date-range'),
###########################################
      path('eventsByDateRange/',
           views.EventsByDateRange.as_view(),
           name='events-by-date-range'),
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
      path('procedure/',
           views.ProcedureList.as_view(),
           name='procedure-list'),
      path('procedure/<int:pk>/',
           views.ProcedureDetail.as_view(),
           name='procedure-detail'),
      path('eventreports/',
            views.EventReportList.as_view(),
            name='eventreport-list'),
      path('eventreports/<int:pk>/',
            views.EventReportDetail.as_view(),
            name='eventreport-detail'),
            
      # based on Report Project.docx      
      path('eventreports/<int:pk>/generate-pdf/', views.EventReportGeneratePDF.as_view(),
         name='eventreport-generate-pdf'),
      #path('persona/eventreports/<int:pk>/generate-pdf/', views.test_pdf, name='eventreport-generate-pdf'),
      path('eventreports/<int:pk>/download/', views.EventReportDownload.as_view(),
         name='eventreport-download'),


      path('uploads/images/',
           views.upload_images_view),
#     path('upload-pdf/',
 #           PDFUploadView.as_view(),
  #          name='pdf-upload'),

      # Endpoint to get data from Angukar and capture image with flaskapi running on local:8001
      #path('capture/',
       #    views.EventReportImageCapture.as_view(),
        #   name='eventreportimagecapture'),

      path('capture/', views.CaptureImageView.as_view(), name='capture-image'),
      path('temp-images/', views.TemporaryImageList.as_view(), name='temp-image-list'),
     # path('image-from-path-or-field/', views.ImageFromPathOrFieldList.as_view(), name='image_from_path_or_field-list'),
      path('temp-images/<int:pk>/', views.DeleteTemporaryImage.as_view(), name='temp-image-delete'),
      path('temp-images/del-all/', views.DeleteAllTempImage.as_view(), name='temp-image-delete-all'),
      path('events/<int:event_id>/save-images/', views.SaveSelectedImages.as_view(), name='save-selected-images'),
      path('eventreportimage/<int:pk>/', views.EventReportImageDetail.as_view(), name='selected-images-details'),
      path('event/<int:pk>/report-images/', views.RemoteImageList.as_view(), name='remote-images')

      
#      path('capture/<int:pk>/',
 #          views.EventReportImageCapture.as_view(),
  #         name='eventreportimage'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#urlpatterns += [
 #   path('temp-images/', views.TemporaryImageList.as_view(), name='temp-image-list'),
  #  path('temp-images/upload/', views.TemporaryImageUpload.as_view(), name='temp-image-upload'),
   # path("events/<int:event_id>/save-images/", views.SaveSelectedImages.as_view(), name="save-selected-images"),
#]


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
