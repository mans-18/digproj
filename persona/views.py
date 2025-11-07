# pylint: disable=import-error
import os
import threading
import uuid
import boto3
import datetime, json
import logging
from botocore.exceptions import ClientError, ParamValidationError
#from datetime import datetime, timedelta
from rest_framework import generics, status, permissions, mixins, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.reverse import reverse
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from django.utils import timezone
from core.models import (User, Kollege, Event, Persona, GenericGroup,
                        EventReport, Partner, Procedure, Event, EventReport,
                        EventReportImage, TemporaryImage)
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt  # 👈 important
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files.base import ContentFile
from persona.serializers import (UserSerializer,
                                 KollegeSerializer,
                                 PersonaSerializer,
                                 EventSerializer,
                                 EventReportSerializer,
                                 EventReportImageSerializer,
                                 TemporaryImageSerializer,
                                 PutEventReportImageSerializer,
                                 PartnerSerializer,
                                 ProcedureSerializer,
                                 GenericGroupSerializer,
                                 EmailFromSiteSerializer)
from persona.utils.report_pdf import build_pdf_for_eventreport, sign_pdf_bytes_if_configured
from persona.permissions import IsSuperOrReadOnly

"""
s3 = boto3.client('s3')

def generate_signed_url(file_field, expires_in=3600):
    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": file_field.name  # file_field.name is the S3 key
        },
        ExpiresIn=expires_in
    )
"""

logger = logging.getLogger(__name__)

s3 = boto3.client('s3')

def generate_signed_url(file_field, expires_in=7257600):
    """
    Safely generate a presigned URL for an S3 file. 
    Returns None if the key is missing, invalid, or AWS rejects the request.
    """
    try:
        key = getattr(file_field, "name", None)
        if not key or not key.strip():
            logger.warning("Skipping presigned URL: empty or invalid S3 key")
            return None

        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": key
            },
            ExpiresIn=expires_in
        )
        return url

    except (ClientError, ParamValidationError) as e:
        logger.error(f"Presigned URL error for key '{key}': {e}")
        return None



class EventReportGeneratePDF(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def post(self, request, pk):
        event_report = get_object_or_404(EventReport, pk=pk)

# authorization: allow staff/partner who owns the kollege or superuser
        if not (request.user.is_staff or request.user.is_superuser or request.user.is_partner):
            return Response({"detail": "Ação não autorizada."}, status=status.HTTP_403_FORBIDDEN)

        image_ids = request.data.get("selected_ids")
        eventReport_id = request.data.get("eventReport_id")
        current_user_name = request.data.get("current_user") or getattr(request.user, "email", None)
        sign = bool(request.data.get("sign", False))

#Optional: logo / signature image fields (store them in GenericGroup or a SiteConfig model if you want)
        logo_field = None     # e.g. settings.SITE_LOGO_FILEFIELD if you add one
        signature_field = None  # e.g. kollege.signature_image if you add an ImageField

        # download_report returns an HttpResponse
        # Gets the type error: "a bytes-like object is required, not 'HttpResponse'"
#        pdf_bytes = download_report(    #build_pdf_for_eventreport(
 #           '',86,
#            selected_images=image_ids,
 #           logo_image_field=logo_field,
  #          signature_image_field=signature_field,
   #         current_user_name=current_user_name,
  #      )

        # This version produces a blob in a new page
        # Also saves a report named "event_340_report_98.pdf" to S3 where one can download from
        # Original
        pdf_bytes = build_pdf_for_eventreport(
            event_report,
            selected_images=image_ids,
            logo_image_field=logo_field,
            signature_image_field=signature_field,
            current_user_name=current_user_name,
        )
        

        if sign and getattr(settings, "PDF_P12_PATH", None):
            pdf_bytes = sign_pdf_bytes_if_configured(
                pdf_bytes,
                p12_path=settings.PDF_P12_PATH,
                p12_password=getattr(settings, "PDF_P12_PASSWORD", "")
            )

        # Save to S3 via FileField (path: reports/%Y/%m/%d/pdfs/)
        #filename = f"event_{event_report.event_id}_report_{event_report.pk}_{event_report.event.start}.pdf"
        filename = f"event_{event_report.event_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"        
        event_report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)

        data = EventReportSerializer(event_report, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)

        
class EventReportDownload(APIView):
  #  permission_classes = [permissions.IsAuthenticated]
   # authentication_classes = (TokenAuthentication,)

    """
    GET /eventreports/<id>/download/
    -> { "url": "<presigned>" }
    """
    def get(self, request, pk):
        event_report = get_object_or_404(EventReport, pk=pk)
        if not event_report.pdf_file:
            return Response({"detail": "O PDF do laudo não foi gerado."}, status=status.HTTP_404_NOT_FOUND)

        # AuthZ as you need; here we allow staff, partner, or the kollege attached to event via email header
       # if not (request.user.is_staff or request.user.is_superuser or request.user.is_partner):
        #    return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME)
            #'s3', region_name=getattr(settings, "AWS_S3_REGION_NAME", None))
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': event_report.pdf_file.name},
            ExpiresIn=5 * 60  # 5 minutes
        )
        return Response({"url": url}, status=status.HTTP_200_OK)


class CaptureImageView(APIView):
    """
    Receives image + metadata from local FastAPI.
    Saves to S3 (and optionally local temp folder).
    """

    def post(self, request, *args, **kwargs):
        print('request data at view', request.data)
        eventid = request.data.get("eventid", "noevent")
        caption = request.data.get("caption", "")
        comment = request.data.get("comment", "")
        image_file = request.FILES.get("image_file")

        if not image_file:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            filename = image_file.name
            temp_img = TemporaryImage(caption=caption, comment=comment)
            temp_img.image_file.save(filename, image_file, save=False)

            # Save locally too (optional)
            
            local_folder = getattr(settings, "TEMP_IMAGE_LOCAL_PATH", "/tmp/temp_images/")
            os.makedirs(local_folder, exist_ok=True)
            local_path = os.path.join(local_folder, filename)
            with open(local_path, "wb") as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            temp_img.local_path = local_path
            temp_img.save()
            
            serializer = TemporaryImageSerializer(temp_img, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TemporaryImageList(APIView, mixins.DestroyModelMixin):
    #permission_classes = [permissions.IsAuthenticated]
    #authentication_classes = (TokenAuthentication,)

    def get(self, request):
        temp_images = TemporaryImage.objects.all().order_by('-uploaded_at')[:200]  # limit to recent
        serializer = TemporaryImageSerializer(temp_images, many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, *arg, **kwargs):
        return self.create(request, *arg, **kwargs)
    
    # Used to delete all temp images at temp-image-list compoent init
    def delete(self, request, *args, **kwargs):
        TemporaryImage.objects.all().delete()
        return Response({"detail": "All temporary images deleted"}, status=status.HTTP_204_NO_CONTENT)


class RemoteImageList(APIView, ):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, pk):
        remote_images = []
        eventid = request.data.get('eventid')
        remoteEvent = get_object_or_404(Event, pk=pk)
        print('remote start',remoteEvent.start)
        ims = remoteEvent.images.all()
        for i in ims:
            remote_images.append(i)
            print('i in views loop', i)
        serializer = EventReportImageSerializer(remote_images, many=True, context={'request': request})
        return Response(serializer.data)

 
class DeleteTemporaryImage(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def delete(self, request, pk):
        print('pk at deleteTemp Im', pk, self)
        temp = get_object_or_404(TemporaryImage, pk=pk)
        temp.image_file.delete(save=False)
        temp.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DeleteAllTempImage(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def delete(self, request):
        ids = request.data.get("ids", [])
        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": "You must provide a non-empty list of ids"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch queryset
        images = TemporaryImage.objects.filter(id__in=ids)

        # Delete associated files
        for img in images:
            img.image_file.delete(save=False)

        # Delete DB rows in bulk
        images.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

""""
""" """ Did not solve duplication """ """
from django.core.files.base import ContentFile
from django.db.models import Q

class SaveSelectedImages(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def post(self, request, event_id):
        image_ids = request.data.get("image_ids", [])
        image_caption = request.data.get("caption", "")
        image_comment = request.data.get("comment", "")
        event = get_object_or_404(Event, pk=event_id)

        saved = []
        temps = TemporaryImage.objects.filter(id__in=image_ids)

        s3_uploaded_keys = set()

        for t in temps:
            filename = os.path.basename(t.image_file.name)
            s3_key = f"events/{event_id}/{filename}"

            # Avoid duplicates
            if EventReportImage.objects.filter(
                Q(event=event) & Q(image_file=s3_key)
            ).exists():
                print(f"Skipping duplicate S3 key: {s3_key}")
                continue

            # Create the DB record first
            event_img = EventReportImage(
                event=event,
                caption=image_caption or t.caption or "",
                comment=image_comment or t.comment or "",
                local_path=None,  # not needed now
            )

            # Upload directly to S3 using ContentFile
            file_bytes = t.image_file.read()
            event_img.image_file.save(s3_key, ContentFile(file_bytes), save=True)

            saved.append({
                "id": event_img.id,
                "s3_key": event_img.image_file.name,
            })

            # Delete local temp file and row
            try:
                t.image_file.delete(save=False)
            except Exception:
                pass
            t.delete()

        return Response({"saved": saved}, status=status.HTTP_201_CREATED)
"""


from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from core.models import Event, TemporaryImage, EventReportImage
import os

class SaveSelectedImages(generics.GenericAPIView):
    """
    POST /api/events/<event_id>/save-images/
    payload example 1 (current):
        {"image_ids": [1, 2, 3], "caption": "text", "comment": "text"}

    payload example 2 (optional future):
        {"images": [{"id": 1, "caption": "x"}, {"id": 2, "caption": "y"}]}
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        image_ids = request.data.get("image_ids", [])
        caption = request.data.get("caption", "")
        comment = request.data.get("comment", "")
        images_data = request.data.get("images", None)  # optional future support
        report_id = request.data.get("report_id", None)

        saved = []
        if not image_ids and not images_data:
            return Response({"error": "No image IDs provided"}, status=400)

        # if per-image data is provided (future-proof)
        if images_data:
            temps = TemporaryImage.objects.filter(id__in=[i["id"] for i in images_data])
            caption_map = {i["id"]: i.get("caption", "") for i in images_data}
            comment_map = {i["id"]: i.get("comment", "") for i in images_data}
        else:
            temps = TemporaryImage.objects.filter(id__in=image_ids)
            caption_map = {t.id: caption for t in temps}
            comment_map = {t.id: comment for t in temps}

        for t in temps:
            filename = os.path.basename(t.image_file.name)

            # ✅ Skip duplicates (same file already linked to this event)
            if EventReportImage.objects.filter(event=event, image_file__icontains=filename).exists():
                continue

            # Create target record
            event_img = EventReportImage.objects.create(
                event=event,
                caption=caption_map.get(t.id, ""),
                comment=comment_map.get(t.id, ""),
                local_path=t.local_path
            )

            # Save actual file to S3
            file_bytes = t.image_file.read()
            s3_filename = f"events/{event_id}/{filename}"
            event_img.image_file.save(s3_filename, ContentFile(file_bytes), save=True)

            saved.append({
                "event_image_id": event_img.id,
                "s3_path": event_img.image_file.name,
                "s3_url": None  # optional: add presigned URL
            })

            # Clean up temporary file and record
            try:
                t.image_file.delete(save=False)
            except Exception:
                pass
            t.delete()

        return Response({"saved": saved}, status=status.HTTP_201_CREATED)
'''
class SaveSelectedImages(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        generics.GenericAPIView):
    """
    POST /api/events/<event_id>/save-images/
    payload: {"image_ids": [1,2,3], "report_id": optional}
    Copies images to EventReportImage (which uses DEFAULT_FILE_STORAGE -> S3),
    then deletes temporary local copies.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = (TokenAuthentication,)

    #queryset = SaveSelectedImages.objects.all()

    def get(self,request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, event_id):
        image_ids = request.data.get("image_ids", [])
        image_caption = request.data.get("caption", '')
        image_comment = request.data.get("comment", '')
        print('image cap and comm', image_ids, image_caption, image_comment)
        report_id = request.data.get("report_id", None)  # optional, if you want to link to EventReport

        event = get_object_or_404(Event, pk=event_id)
        saved = []

        temps = TemporaryImage.objects.filter(id__in=image_ids)
        for t in temps:
            # create EventReportImage (this model saves to default storage i.e., S3)
            # Bad previous code set caption=t.caption
            event_img = EventReportImage.objects.create(event=event, caption=image_caption or '', comment=image_comment or '', local_path=t.local_path)
            # read local file and save into the EventReportImage.image_file which uses S3
            """
            
            '''''' ✅ Better: use Django’s built-in File object directly — no manual read into memory. You can stream from disk to S3:''''''
            filename = f"events/{event_id}/{os.path.basename(t.image_file.name)}"
            with t.image_file.open("rb") as f:
                event_img.image_file.save(filename, f, save=True)
            """
            ############# Saves to S3 without reopening the file as above ###########
            ############# Expensive for multi MB files 
            filename = f"events/{event_id}/{os.path.basename(t.image_file.name)}"
            # Get the bytes of the file directly
            file_bytes = t.image_file.read()  
            # Wrap in ContentFile and save to S3
            event_img.image_file.save(filename, ContentFile(file_bytes), save=True)
            ################################################
            
            saved.append({
                "event_image_id": event_img.id,
                "s3_path": event_img.image_file.name,
                "s3_url": None  # if you want, generate presigned URL and return it
            })

            # delete local temp file and db row
            try:
                t.image_file.delete(save=False)
            except Exception:
                pass
            t.delete()

        return Response({"saved": saved}, status=status.HTTP_201_CREATED)
'''



    #########3 To  include caption and comment 11-10-25
class EventReportImageDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    permission_classes =[permissions.IsAuthenticated,]

    queryset = EventReportImage.objects.all()
    serializer_class = PutEventReportImageSerializer

    authentication_classes = (TokenAuthentication,)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)
        

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'kollegen': reverse('kollege-list', request=request, format=format),
        'personas': reverse('persona-list', request=request, format=format),
        'events': reverse('event-list', request=request, format=format),
        'genericgroup': reverse('genericgroup-list', request=request, format=format),
        'partners': reverse('partner-list', request=request, format=format),
        'eventreports': reverse('eventreport-list', request=request, format=format),
    })

    ############################################
    ''' From ChatGPT 10-08-25'''

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def upload_images_view(request):
    """
    Accepts multiple files with key 'images' and required event_id.
    Optionally include report_id to attach to an existing report.
    Returns list of created EventReportImage objects (serialized).
    """
    event_id = request.data.get('event_id')
    report_id = request.data.get('report_id')
    if not event_id:
        return Response({"detail": "event_id required"}, status=status.HTTP_400_BAD_REQUEST)
    event = get_object_or_404(Event, id=event_id)
    report = None
    if report_id:
        report = get_object_or_404(EventReport, id=report_id)

    created = []
    for f in request.FILES.getlist('images'):
        eri = EventReportImage.objects.create(event=event, report=report, image_file=f, caption=f.name)
        created.append(eri)

    serializer = EventReportImageSerializer(created, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)













from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import Persona, Event


'''
class EmailKollege(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = Event.objects.filter(start__gte=date.today())
    serializer_class = EventSerializer

    # @xframe_options_exempt
    def email_kollege(self, request, *args, **kwargs):
            
            toEmail = ['digest.principal@gmail.com',]
            kolIds = []
            kolListToMail = json.loads(request.body.decode())
            for item in kolListToMail:
                toEmail.append(item['email'])
                kolIds.append(item['id'])
            toEmailCount = len(toEmail)

            qs = Event.objects.order_by('start').filter(
            start__date=date.today()+datetime.timedelta(days=1)).values()
            lqs = list(qs)
            ps = Persona.objects.filter(
            event_persona__start__date=date.today()+datetime.timedelta(days=1)).values()
            lps = list(ps)

            psToEmail = []
            for p in lps:
                for q in lqs:
                    if p['id'] == q['persona_id']:
                        if q['kollege_id'] == json.loads(request.body.decode())[0]['id']:
                            psToEmail.append(p)

            extra = json.loads(request.body.decode())[0]['name'] #''

            msg_html = render_to_string('email2.html', {'event_data':lqs, 'persona_data':lps, #'per_name':per_name,
                                        'kollege_id':json.loads(request.body.decode())[0]['id'],
                                        'psToEmail': psToEmail,
                                        'extra': extra, 'toEmailCount':toEmailCount})

            template_email_text = 'hi'
            return send_mail('Digest email',
                            template_email_text,
                            'miguel.sza1@gmail.com',
                            toEmail,
                            html_message=msg_html,
                            fail_silently=False)
    
    def post(self, request, *args, **kwargs):

        self.email_kollege(request)
        return self.list(request, *args, **kwargs)
'''
        

'''

# views.py
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import Event, Persona, Kollege  # adjust imports as needed
import json


class EmailKollege(APIView):
    """
    Sends tomorrow's schedule to selected colleagues.
    """
    def post(self, request):
        try:
            # Parse input only once
            kol_list = request.data  # DRF parses JSON automatically
            if not kol_list:
                return Response({"detail": "Nenhum colega informado."}, status=400)

            to_emails = ['digest.principal@gmail.com']
            kol_ids = [k['id'] for k in kol_list if 'id' in k]
            kol_names = {k['id']: k.get('name', '') for k in kol_list if 'id' in k}
            to_emails.extend([k['email'] for k in kol_list if k.get('email')])
            to_email_count = len(to_emails)

            tomorrow = date.today() + timedelta(days=1)

            # Filter only needed events (kollege + tomorrow)
            events = (
                Event.objects
                .filter(start__date=tomorrow, kollege_id__in=kol_ids)
                .select_related('persona', 'kollege')
                .order_by('start')
            )

            if not events.exists():
                return Response({"detail": "Nenhum evento encontrado para amanhã."}, status=204)

            # Build per-kollege email content
            sent = 0
            for kol_id in kol_ids:
                kol_events = [ev for ev in events if ev.kollege_id == kol_id]
                if not kol_events:
                    continue

                persona_data = [
                    {
                        "name": ev.persona.name,
                        "start": ev.start,
                        "title": ev.title,
                        "color": ev.color,
                    }
                    for ev in kol_events
                ]

                context = {
                    "event_data": kol_events,
                    "persona_data": persona_data,
                    "kollege_id": kol_id,
                    "extra": kol_names[kol_id],
                    "toEmailCount": to_email_count,
                }

                msg_html = render_to_string('email2.html', context)
                send_mail(
                    subject=f"Agenda de amanhã - {kol_names[kol_id]}",
                    message="Veja sua agenda de amanhã.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[k['email'] for k in kol_list if k['id'] == kol_id and k.get('email')],
                    html_message=msg_html,
                    fail_silently=False,
                )
                sent += 1

            return Response({"detail": f"E-mails enviados: {sent}"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
'''


# Functionaing manual class

class EmailKollege(APIView):
    """
    Sends tomorrow's schedule to selected colleagues in a background thread.
    """
    def post(self, request):
        kol_list = request.data
        if not kol_list:
            return Response({"detail": "Nenhum colega informado."}, status=400)

        # Launch email sending in a separate thread
        thread = threading.Thread(target=self.send_emails, args=(kol_list,))
        thread.start()

        return Response({"detail": "Emails are being sent in the background."}, status=status.HTTP_202_ACCEPTED)

    def send_emails(self, kol_list):
        tomorrow = date.today() + timedelta(days=1)
        kol_ids = [k['id'] for k in kol_list if 'id' in k]
        kol_email_map = {k['id']: k.get('email') for k in kol_list if 'id' in k}
        kol_name_map = {k['id']: k.get('name', '') for k in kol_list if 'id' in k}
        cc_email = "digest.principal@gmail.com"
        
        # Fetch all events for tomorrow for selected colleagues
        events = (
            Event.objects
            .filter(start__date=tomorrow, kollege_id__in=kol_ids)
            .select_related('persona')  # avoids extra queries for persona
            .order_by('start')
        )

        # Group events by kollege_id
        events_by_kollege = {}
        for ev in events:
            events_by_kollege.setdefault(ev.kollege_id, []).append(ev)

        # Send emails per colleague
        for kol_id, kol_events in events_by_kollege.items():
            email = kol_email_map.get(kol_id)
            if not email:
                continue

            # Build persona/event data for template
            persona_data = [
                {
                    "name": ev.persona.name,
                    "start": ev.start,
                    "title": ev.title,
                    "color": ev.color,
                }
                for ev in kol_events
            ]

            context = {
                "event_data": kol_events,
                "persona_data": persona_data,
                "kollege_id": kol_id,
                "extra": kol_name_map.get(kol_id, ""),
                "toEmailCount": len(kol_list) + 1,
            }

            msg_html = render_to_string('email2.html', context)

            try:
                send_mail(
                    subject=f"Agenda de amanhã - {kol_name_map.get(kol_id, '')}",
                    message="Segue sua agenda de amanhã.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email] + [cc_email],
                    html_message=msg_html,
                    fail_silently=False,
                )
            except Exception as e:
                # Optionally log the error
                print(f"Failed to send email to kollege_id {kol_id}: {e}")


class EmailFromSite(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    generics.GenericAPIView):

    def get_queryset(self):
        req = self.request.data
        print(req)
        name = req['name']
        mobile = req['mobile']
        email = req['email']
        body = req['body']
        return req
    serializer_class = EmailFromSiteSerializer

    # @xframe_options_exempt
    def emailFromSite(self, request, *args, **kwargs):
            toEmail = ['miguel.sza@gmail.com', 'digest.principal@gmail.com', 'contato@digest.com.br',]
            #print(request.body.decode())
            req = json.loads(request.body.decode())
            #print('req', req)
            if req['name']:
                name = req['name']
            else:
                name = 'em branco'
            if req['mobile']:
                mobile = req['mobile']
            else:
                mobile = 'em branco'
            if req['email']:
                email = req['email']
            else:
                email = 'em branco'
            if req['body']:
                body = req['body']
            else:
                body = 'em branco'
            #msg_html = render_to_string('emailFromSite.html', {'name': name, 'mobile': mobile, 'email': email, 'body': body}, )
            msg_html = render_to_string('emailFromSite.html', {'name': name, 'mobile': mobile, 'email': email, 'body': body}, )
            template_email_text = 'Cliente: ' + name + \
            '/ '+ mobile + '/ ' + email + '/ ' + body
            print(name)
            return send_mail('Email do site',
                            template_email_text,
                            'miguel.sza@gmail.com',
                            toEmail,
                            html_message=msg_html)
    
    def post(self, request, *args, **kwargs):
        self.emailFromSite(request)
        return self.list(request, *args, **kwargs)


## Allows an endpoint to get and post users
## Added after creating User model (27/5/24) and adding is_limited, is_partner, is_staff
class UserList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        txt = request.headers
        print('request.data',txt)

        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class UserDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = User.objects.all()
    serializer_class = UserSerializer

    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)


class KollegeList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes =[permissions.IsAuthenticated,]
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly,]
    # pylint: disable=no-member
    queryset = Kollege.objects.all()
    serializer_class = KollegeSerializer

    # If active, auth is done with token sent in the header (by ModHeader) and actions are activated
    authentication_classes = (TokenAuthentication,)

    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'crm']

    def get(self, request, *args, **kwargs):

        #### TO ACCESS DATA FROM THE FRONT-END ####
        #### MAY YIELD AN AGENDA ON THE FRONTEND REQUEST AND RETRIEVE IT HERE ####
        txt = request.headers # MAY BE .data, .body, .GET?POST?PUT?PATCH? 

        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # self.email_kollege(request)
        #The error is not passed to the client
            if request.user.is_superuser:
                return self.create(request, *args, **kwargs)
            raise AssertionError('Usuário sem permissão para criar um kollege!')

class KollegeDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = Kollege.objects.all()
    serializer_class = KollegeSerializer

    authentication_classes = (TokenAuthentication,)

    #permission_classes =[permissions.IsAdminUser,]
    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticated,]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)
        raise AssertionError('Usuário sem permissão para deletar')

class PartnerList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticated,]
    # pylint: disable=no-member
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    authentication_classes = (TokenAuthentication,)

    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'crm']

    def get(self, request, *args, **kwargs):
        txt = request.headers

        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class PartnerDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer

    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)
        
class ProcedureList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticated,]
    # pylint: disable=no-member
    queryset = Procedure.objects.all()
    serializer_class = ProcedureSerializer
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        txt = request.headers
        print('request.data',txt)

        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class ProcedureDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = Procedure.objects.all()
    serializer_class = ProcedureSerializer

    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)

class PersonaList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes =[permissions.IsAuthenticated,]

    queryset = Persona.objects.all()

    serializer_class = PersonaSerializer

    # Needed to search from the url
    filter_backends = [filters.SearchFilter]
    search_fields = ['name','dob','email','mobile']

    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class PersonaListLimited(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes =[permissions.IsAuthenticated,]
    

    def get_queryset(self):
        user_email = self.request.META.get('HTTP_CURRENTUSER')
        #print('user_email at personalistlimited',user_email)
        kollege_with_email = (Kollege.objects.filter(email=user_email))
        #print('qsKol at perLimited:', kollege_with_email)
        if (kollege_with_email):
            #Fetch fresh data each time the view is accessed
            return list(set(Persona.objects.filter(
            event_persona__start__gt=date.today()-timedelta(days=30),
            event_persona__start__lte=date.today()+timedelta(days=30))))
        else:
            return list(set(Persona.objects.filter(
            event_persona__start__gt=date.today()-timedelta(days=180),
            event_persona__start__lte=date.today()+timedelta(days=180))))
         

    serializer_class = PersonaSerializer

    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'mobile']

    authentication_classes = (TokenAuthentication,)

    # The decorator (do not) prevents the persona column on event.component being empty when creting a new event.
    # Without it, the column would only be filled (defined) if the gunicorn serve was restarted.
    @method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True))
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class PersonaDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    permission_classes =[permissions.IsAuthenticated,]

    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer

    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)

class EventList(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                generics.GenericAPIView):

    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)
    
    def get_queryset(self):
        # Custom header at getAuthHeaders() in Angular api.service
        user_email = self.request.META.get('HTTP_CURRENTUSER')
        kollege_with_email = (Kollege.objects.filter(email=user_email))
        if (kollege_with_email):
            queryset = Event.objects.filter(kollege_id=kollege_with_email.first())
            return queryset
        else:
            queryset = Event.objects.all()
            return queryset

    
    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.create(request, *args, **kwargs)


class EventListLimited(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                generics.GenericAPIView):
    
    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)
#############
    def get_queryset(self):
        user_email = self.request.META.get('HTTP_CURRENTUSER')
        kollege_with_email = (Kollege.objects.filter(email=user_email))
        if (kollege_with_email):
            queryset = Event.objects.filter(kollege_id=kollege_with_email.first()).filter(
                start__gte=date.today()-timedelta(days=1),
                start__lte=date.today()+timedelta(days=60)).exclude(status='cancelado')
            return queryset
        else:
            queryset = Event.objects.filter(
            start__gte=date.today()-timedelta(days=90),
            start__lte=date.today()+timedelta(days=60)).exclude(status='cancelado')
            return queryset

    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        # print('user ', request.user)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # print('user ', request.user)
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.create(request, *args, **kwargs)


class EventsByDateRange(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                generics.GenericAPIView):
    
    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        user_email = self.request.META.get('HTTP_CURRENTUSER')
        kollege_with_email = (Kollege.objects.filter(email=user_email))
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if (kollege_with_email):
            format_str = '%d/%m/%Y'
            queryset = Event.objects.filter(kollege_id=kollege_with_email.first()).filter(
                start__gte = datetime.datetime.strptime(start_date, format_str),
                start__lte=datetime.datetime.strptime(end_date, format_str)).exclude(status='cancelado')
            return queryset
        else:
            format_str = '%d/%m/%Y'
            queryset = Event.objects.filter(
                start__gte = datetime.datetime.strptime(start_date, format_str),
                start__lte=datetime.datetime.strptime(end_date, format_str)).exclude(status='cancelado')
            return queryset


    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.create(request, *args, **kwargs)


class EventDetail(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  generics.GenericAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)


class GenericGroupList(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    queryset = GenericGroup.objects.all()
    serializer_class = GenericGroupSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class GenericGroupListDetail(mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             generics.GenericAPIView):
    queryset = GenericGroup.objects.all()
    serializer_class = GenericGroupSerializer

    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)


class EventReportList(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)



    def get_queryset(self):
        '''
        Get the currentuser as user_email from the request custom header set on getAuthHeaders() on api.service.ts;
        Get the kolleges with the email "user_emaiL" (should be only one, except if duplicated);
        If there is a kollege_with_email, return eventreport queryset limited to the reports of the events which kollege_id's are kollege_with_email;
        If there is not a kollege_with_email, return an eventreport queryset of all reports limited to a period.
        tips:
        To keep consistency in querysets, kollege_with_email.first() better than index kollege_with_email[0];
        Custom header must be stated on settings.py: CORS_ALLOW_HEADERS = list(default_headers) + ['CurrentUser',]

        '''
        user_email = self.request.META.get('HTTP_CURRENTUSER')
        kollege_with_email = (Kollege.objects.all().filter(email=user_email))

        if kollege_with_email.exists():
            queryset = EventReport.objects.all().filter(event__kollege_id=kollege_with_email.first())            
            return queryset

        else:
            queryset = EventReport.objects.all()
            return queryset
        
    serializer_class = EventReportSerializer


    def get(self, request, *args, **kwargs):
        if request.user.is_staff or request.user.is_partner:
            # print('user ', request.user)
            return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # print('user ', request.user)
        return self.create(request, *args, **kwargs)



from django.core.cache import cache

class EventReportById(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = EventReportSerializer

    def get_queryset(self):
        event_id = self.kwargs.get('pk')
        cache_key = f"event_report_{event_id}"

        # ✅ Try cached data first
        cached_qs = cache.get(cache_key)
        if cached_qs:
            print("💾 Using cached EventReport queryset")
            return cached_qs

        # ✅ Query and optimize only via select_related('event')
        queryset = (
            EventReport.objects
            .filter(event__id=event_id)
            .select_related('event')  # Valid optimization
        )

        # ✅ Cache evaluated queryset list for 2 minutes
        data = list(queryset)
        cache.set(cache_key, data, timeout=120)

        print(f"📊 Cached {len(data)} EventReport(s) for event {event_id}")
        return data

    def get(self, request, *args, **kwargs):
        if request.user.is_staff or getattr(request.user, 'is_partner', False):
            return self.list(request, *args, **kwargs)
        return Response(
            {"detail": "Not authorized."},
            status=status.HTTP_403_FORBIDDEN
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        event_id = instance.event.id if instance.event else None
        if event_id:
            cache.delete(f"event_report_{event_id}")  # invalidate cache on new entry
        return instance



'''
class EventReportById(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = EventReportSerializer

    def get_queryset(self):
        event_id = self.kwargs.get('pk')
        cache_key = f"event_report_{event_id}"

        # Try cached version
        cached_data = cache.get(cache_key)
        if cached_data:
            print("💾 Returning cached queryset")
            return cached_data

        # Get from DB (optimize only with select_related)
        queryset = (
            EventReport.objects
            .filter(event__id=event_id)
            .select_related('event')  # Only if 'event' is a FK
        )

        # Evaluate queryset (important: force query)
        data = list(queryset)
        cache.set(cache_key, data, timeout=120)  # 2 minutes

        return data

    def get(self, request, *args, **kwargs):
        if request.user.is_staff or getattr(request.user, 'is_partner', False):
            return self.list(request, *args, **kwargs)
        return Response(
            {"detail": "Not authorized."},
            status=status.HTTP_403_FORBIDDEN
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        event_id = instance.event.id if instance.event else None
        if event_id:
            cache.delete(f"event_report_{event_id}")  # invalidate cache
        return instance
    

class EventReportById(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                generics.GenericAPIView):
    
    permission_classes = [permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    serializer_class = EventReportSerializer
    
    def get_queryset(self):
        print('request event_id: ', self.request)
        print('self.kwargs', self.kwargs['pk'])
        event_id = self.kwargs.get('pk')
        queryset = EventReport.objects.filter(
            event__id=event_id)
        print('queryset in get_queryset', queryset)
        return queryset
    
    def get(self, request, *args, **kwargs):
        if request.user.is_staff or getattr(request.user, 'is_partner', False):
            return self.list(request, *args, **kwargs)
        else:
            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN
            )
'''  

####################'''TODO'''##############################################
class EventReportListLimited(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                generics.GenericAPIView):
    
    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)
#############
    def get_queryset(self):

        user_email = self.request.META.get('HTTP_CURRENTUSER')
        kollege_with_email = (Kollege.objects.filter(email=user_email))
        if (kollege_with_email):
            queryset = EventReport.objects.filter(kollege_id=kollege_with_email[0]).filter(
                event__start__gte=datetime.today()-timedelta(days=5),
                event__start__lte=datetime.today()+timedelta(days=60)).exclude(color='#FFFFFF')
            return queryset
        else:
            queryset = EventReport.objects.filter(
            event__start__gte=datetime.today()-timedelta(days=1),
            event__start__lte=datetime.today()+timedelta(days=7)).exclude(color='#FFFFFF')
            return queryset


    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        # print('user ', request.user)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # print('user ', request.user)
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.create(request, *args, **kwargs)

########################################################################


class EventReportDetail(mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = EventReport.objects.all()
    serializer_class = EventReportSerializer

    permission_classes =[permissions.IsAuthenticated,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if (request.user.is_staff) & (not request.user.is_limited):
            return self.update(request, *args, **kwargs)
        
    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)
