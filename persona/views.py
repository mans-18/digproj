# pylint: disable=import-error
from rest_framework import generics, status, permissions, renderers, mixins, filters
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from persona.permissions import IsSuperOrReadOnly

from django.core.mail import send_mail, EmailMessage
import smtplib, datetime, cgi, json
from email.mime.text import MIMEText
from datetime import timedelta

#import cv2
import argparse

# from django.views.decorators.clickjacking import xframe_options_exempt

import django_filters.rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from django.template.loader import render_to_string

from persona.serializers import (KollegeSerializer,
                                 PersonaSerializer,
                                 EventSerializer,
                                 EventReportSerializer,
                                 PartnerSerializer,
                                 GenericGroupSerializer,
                                 EmailFromSiteSerializer)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpRequest, HttpResponse

from collections import defaultdict

from core.models import Kollege, Event, Persona, GenericGroup, EventReport, Partner

from persona import serializers


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        #'users': reverse('user-list', request=request, format=format),
        'kollegen': reverse('kollege-list', request=request, format=format),
        'personas': reverse('persona-list', request=request, format=format),
        'events': reverse('event-list', request=request, format=format),
        'genericgroup': reverse('genericgroup-list', request=request, format=format),
        'partners': reverse('partner-list', request=request, format=format),
        'eventreports': reverse('eventreport-list', request=request, format=format),
    })

class EmailKollege(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = Event.objects.filter(start__gte=datetime.date.today())
    serializer_class = EventSerializer

    # @xframe_options_exempt
    def email_kollege(self, request, *args, **kwargs):
            # id = request.POST.get('id')
            # id = request.PUT.get('id')
            # kollege = Kollege.objects.get(id=id)
            # Error: template does not exist
            # qs = Event.objects.filter(start__gte=datetime.date.today())
            # data = defaultdict(list)
            # for title, start in qs.values_list('title', 'start'):
            #     data[title].append(start)
            # print(data

            toEmail = []
            kolIds = []
            # Decodes the bytes obj to a str, and parses it to a json dict
            # "multiple" at the dashboard html delivers a dictionary. Without it, delivers a list of keys
            # kolListToMail = json.loads(request.body)   # does it as a stream, as well apparently
            kolListToMail = json.loads(request.body.decode())
            for item in kolListToMail:
                # Append a dict value
                toEmail.append(item["email"])
                kolIds.append(item['id'])
                #print(kolListToMail, kolIds, toEmail)
            print('request body count', len(request.body.decode()))
            print('toEmail count', len(toEmail))
            toEmailCount = len(toEmail)
            #print('toEmail', toEmail)

            qs = Event.objects.order_by('start').filter(
            start__date=datetime.date.today()+timedelta(days=1)).values()
            lqs = list(qs)

            ps = Persona.objects.all().values()
            lps = list(ps)

            kl = Kollege.objects.all().values()
            lkl = list(kl)
            #print('This lkl',lkl)

            ##### Shows a list of events from a single kollege ####
            eventList = []
            for ev in lqs:
                if ev['kollege_id'] in kolIds: #== 1:
                    eventList.append(ev)
            #print('eventList', eventList)

            extra = ''
            for koltotal in lkl:
                for kol in kolIds:
                    #for ev in lqs:
                        #for pers in lps:
                           # if kol == ev['kollege_id']:
                                #if pers['id'] == ev['persona_id']:
                                    if koltotal['id'] == kol:
                                        extra = koltotal['name']
            print('this extra', extra)

            #### This is done on the template ######
            # mailList_p = []
            # for ev in lqs:
            #     for item in lps:
            #         if item['id'] == ev['persona_id']:
            #             mailList_p.append(item)

            msg_html = render_to_string('email.html', {'event_data':eventList, 'persona_data':lps,
                                        'kollege_data':lkl, 'extra': extra, 'toEmailCount':toEmailCount})
            # return send_mail('Digest Agenda',
            #     msg_html,
            #     'miguel.sza@gmail.com',
            #     toEmail,
            #     fail_silently=False,
            #     )
            template_email_text = 'hi'
            return send_mail('Digest email',
                            template_email_text,
                            'miguel.sza@gmail.com',
                            toEmail,
                            html_message=msg_html)
    
    def post(self, request, *args, **kwargs):
        # id = []
        # # Decodes the bytes obj to a str, and parses it to a json dict
        # for item in json.loads(request.body.decode()):
        #     # Append a dict value
        #     id.append(item['id'])
        # print(json.loads(request.body.decode()), id)
        self.email_kollege(request)
        return self.list(request, *args, **kwargs)

class EmailFromSite(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    generics.GenericAPIView):

    # pylint: disable=no-member

    #AssertionError: 'EmailFromSite' should either include a `queryset` attribute, 
    # or override the `get_queryset()` method.
    def get_queryset(self):
        #req = json.loads(self.request.body.decode())
        #req = self.request.body
        req = self.request.data
        print(req)
        name = req['name']
        mobile = req['mobile']
        email = req['email']
        body = req['body']
        emailTxt = name + mobile + email + body
        #print(emailTxt)
        #return emailTxt
        return req
    #queryset = {}#Event.objects.filter(start__gte=datetime.date.today())
    # May override get_serializer
    serializer_class = EmailFromSiteSerializer

    # @xframe_options_exempt
    def emailFromSite(self, request, *args, **kwargs):
            toEmail = ['miguel.sza@gmail.com', 'contato@digest.com.br']
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


# def sendMail_py(self):
#         # A python wayn to send email
#         # (https://humberto.io/pt-br/blog/enviando-e-recebendo-emails-com-python/)
#         # conexão com os servidores do google
#         smtp_ssl_host = 'smtp.gmail.com'
#         smtp_ssl_port = 465
#         # username ou email para logar no servidor
#         username = 'miguel.sza@gmail.com'
#         password = 'leugim@13'

#         from_addr = 'miguel.sza@gmail.com'
#         to_addrs = ['miguel.sza1@gmail.com']

#         # a biblioteca email possuí vários templates
#         # para diferentes formatos de mensagem
#         # neste caso usaremos MIMEText para enviar
#         # somente texto
#         message = MIMEText('Hello World')
#         message['subject'] = 'Hello'
#         message['from'] = from_addr
#         message['to'] = ', '.join(to_addrs)

#         # conectaremos de forma segura usando SSL
#         server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
#         # para interagir com um servidor externo precisaremos
#         # fazer login nele
#         server.login(username, password)
#         server.sendmail(from_addr, to_addrs, message.as_string())
#         server.quit()

class KollegeList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly,]
    # pylint: disable=no-member
    queryset = Kollege.objects.all()
    serializer_class = KollegeSerializer

    # If active, auth is done with token sent in the header (by ModHeader) and actions are activated
    authentication_classes = (TokenAuthentication,)
    
    # def email_kollege(self, request):
    #     # id = request.POST.get('id')
    #     # id = request.PUT.get('id')
    #     # kollege = Kollege.objects.get(id=id)
    #     # Error: template does not exist
    #     msg_html = render_to_string('email.html', {'kollege': 'kollege'})
    #     template_email_text = 'hi from button'
    #     return send_mail('Lelander work samples',
    #                     template_email_text,
    #                     'miguel.sza@gmail.com',
    #                     ['miguel.sza1@gmail.com'],
    #                     html_message=msg_html)

    # def sendMail_py(self):
    #     # A python wayn to send email
    #     # (https://humberto.io/pt-br/blog/enviando-e-recebendo-emails-com-python/)
    #     # conexão com os servidores do google
    #     smtp_ssl_host = 'smtp.gmail.com'
    #     smtp_ssl_port = 465
    #     # username ou email para logar no servidor
    #     username = 'miguel.sza@gmail.com'
    #     password = 'leugim@13'

    #     from_addr = 'miguel.sza@gmail.com'
    #     to_addrs = ['miguel.sza1@gmail.com']

    #     # a biblioteca email possuí vários templates
    #     # para diferentes formatos de mensagem
    #     # neste caso usaremos MIMEText para enviar
    #     # somente texto
    #     message = MIMEText('Hello World')
    #     message['subject'] = 'Hello'
    #     message['from'] = from_addr
    #     message['to'] = ', '.join(to_addrs)

    #     # conectaremos de forma segura usando SSL
    #     server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
    #     # para interagir com um servidor externo precisaremos
    #     # fazer login nele
    #     server.login(username, password)
    #     server.sendmail(from_addr, to_addrs, message.as_string())
    #     server.quit()

    def get(self, request, *args, **kwargs):
        # Needs to activate apps menos seguros no Google:
        # https://myaccount.google.com/lesssecureapps
        # self.email_kollege(request)

        #### TO ACCESS DATA FROM THE FRONT-END ####
        #### MAY YIELD AN AGENDA ON THE FRONTEND REQUEST AND RETRIEVE IT HERE ####
        txt = request.headers # MAY BE .data, .body, .GET?POST?PUT?PATCH? 
        #print('request.data',txt)

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
    permission_classes =[permissions.IsAuthenticatedOrReadOnly,]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)
        raise AssertionError('Usuário sem permissão para deletar')

class PartnerList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly,]
    # pylint: disable=no-member
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        
        txt = request.headers
        print('request.data',txt)

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
    permission_classes =[permissions.IsAuthenticatedOrReadOnly,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)


class PersonaList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly,]
    # pylint: disable=no-member
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    # filter_backends = [django_filters.rest_framework.DjangoFilterBackend]#(DjangoFilterBackend,)
    # filterset_fields = ('name',)
    # Needed to search from the url
    filter_backends = [filters.SearchFilter]
    search_fields = ['name','dob','email','mobile']

    authentication_classes = (TokenAuthentication,)

    # def get_queryset(self):
    #     name = self.request.query_params.get('name', None)
    #     queryset = Persona.objects.all()
    #     # print(queryset.filter(name__startswith=name))
    #     # print(type(queryset))
    #     if name is None:
    #         return super().get_queryset()
    #     if name is not None:
    #             return queryset.filter(name__contains=name)
    #     return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    # def get_queryset(self):
    #     name = self.request.query_params.get('name', None)
    #     if name is None:
    #         return super().get_queryset()
    #     queryset = Persona.objects.all()
    #     if name.lower() is not None:
    #         return queryset.filter(name__icontains=name)

class PersonaDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer

    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticatedOrReadOnly,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)


class EventList(mixins.ListModelMixin,
                mixins.CreateModelMixin,
                generics.GenericAPIView):
    # pylint: disable=no-member
    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticatedOrReadOnly,]
    authentication_classes = (TokenAuthentication,)

    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get(self, request, *args, **kwargs):
        # print('user ', request.user)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # print('user ', request.user)
        return self.create(request, *args, **kwargs)


class EventDetail(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticatedOrReadOnly,]
    authentication_classes = (TokenAuthentication,)

    ############################################
    '''
    def read_camera_capture(self, index_camera):
        # Import the required packages
        print(index_camera)
        # We first create the ArgumentParser object
        # The created object 'parser' will have the necessary information
        # to parse the command-line arguments into data types.
    #    parser = argparse.ArgumentParser()

        # We add 'index_camera' argument using add_argument() including a help.
    #    parser.add_argument("index_camera", help="index of the camera to read from", type=int)
    #   args = parser.parse_args()

        # We create a VideoCapture object to read from the camera (pass 0):
    #    capture = cv2.VideoCapture(args.index_camera)
        capture = cv2.VideoCapture(index_camera)

        # Get some properties of VideoCapture (frame width, frame height and frames per second (fps)):
        frame_width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = capture.get(cv2.CAP_PROP_FPS)

        # Print these values:
        print("CV_CAP_PROP_FRAME_WIDTH: '{}'".format(frame_width))
        print("CV_CAP_PROP_FRAME_HEIGHT : '{}'".format(frame_height))
        print("CAP_PROP_FPS : '{}'".format(fps))

        # Check if camera opened successfully
        if capture.isOpened() is False:
            print("Error opening the camera")

        # Index to save current frame
        frame_index = 0

        # Read until video is completed
        while capture.isOpened():
            # Capture frame-by-frame from the camera
            ret, frame = capture.read()

            if ret is True:
                # Display the captured frame:
                cv2.imshow('Input frame from the camera', frame)

                # Convert the frame captured from the camera to grayscale:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Display the grayscale frame:
                cv2.imshow('Grayscale input camera', gray_frame)

                # Press c on keyboard to save current frame
                if cv2.waitKey(20) & 0xFF == ord('c'):
                    frame_name = "camera_frame_{}.png".format(frame_index)
                    gray_frame_name = "grayscale_camera_frame_{}.png".format(frame_index)
                    cv2.imwrite(frame_name, frame)
                    cv2.imwrite(gray_frame_name, gray_frame)
                    frame_index += 1

                # Press q on keyboard to exit the program
                if cv2.waitKey(20) & 0xFF == ord('q'):
                    break
            # Break the loop
            else:
                break

        # Release everything:
        capture.release()
        cv2.destroyAllWindows()
    '''
    ####################################################

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)

class GenericGroupList(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       generics.GenericAPIView):
    # pylint: disable=no-member
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,]
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
    # pylint: disable=no-member
    queryset = GenericGroup.objects.all()
    serializer_class = GenericGroupSerializer

    #permission_classes =[IsSuperOrReadOnly, permissions.IsAuthenticatedOrReadOnly,]
    permission_classes =[permissions.IsAuthenticatedOrReadOnly,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.is_staff:
            return self.destroy(request, *args, **kwargs)


class EventReportList(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly,]
    authentication_classes = (TokenAuthentication,)
    # pylint: disable=no-member
    queryset = EventReport.objects.all()
    serializer_class = EventReportSerializer

    def get(self, request, *args, **kwargs):
        # print('user ', request.user)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # print('user ', request.user)
        return self.create(request, *args, **kwargs)


class EventReportDetail(mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    # pylint: disable=no-member
    queryset = EventReport.objects.all()
    serializer_class = EventReportSerializer

    permission_classes =[permissions.IsAuthenticatedOrReadOnly,]
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    #def post(self, request, *args, **kwargs):
    # print('user ', request.user)
     #   return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        #self.read_camera_capture(0)
        if request.user.is_staff:
            return self.update(request, *args, **kwargs)
        
    def delete(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return self.destroy(request, *args, **kwargs)


# # API ORIGINAL, BASEADO NO COURSE RECIPE. ACIMA MODIFICAMOS O VIEW CONFORME O REST/PRODUCT QUE FUNCIONOU COM O PROJ ANGUKAR MOVIE-RATER
# '''
# Formato Browser Api (# em renderer_classes, template_name e return Response(dict))
# '''


# from rest_framework import generics, status, permissions, renderers, mixins
# from rest_framework.response import Response
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
# from rest_framework.response import Response
# from rest_framework.decorators import api_view
# from rest_framework.reverse import reverse

# from persona.serializers import (KollegeSerializer,
#                                  PersonaSerializer,
#                                  EventSerializer)

# from django.shortcuts import render, get_object_or_404, redirect
# from django.http import Http404
# import requests


# from core.models import Kollege, Event, Persona

# from persona import serializers


# @api_view(['GET'])
# def api_root(request, format=None):
#     return Response({
#         #'users': reverse('user-list', request=request, format=format),
#         'kollegen': reverse('kollege-list', request=request, format=format),
#         'personas': reverse('persona-list', request=request, format=format),
#         'events': reverse('event-list', request=request, format=format),
#     })


# class KollegeList(generics.ListCreateAPIView):

#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'inicio.html'

#     permission_classes = [permissions.IsAuthenticatedOrReadOnly,]

#     queryset = Kollege.objects.all()
#     serializer_class = KollegeSerializer

#     # Override: for the view to render on the homexxx.html, the template_name
#     # and the renderer_classes must be set. Also, the get and post methods
#     # must be overriden.
#     def get(self, request, format=None):
#         # gets a queryset
#         kollegen = Kollege.objects.all()
#         # gets a python type (dict)
#         serializer = KollegeSerializer(kollegen, many=True)
#         return Response({'serializer': serializer, 'kollegen': kollegen})
#         #return Response(serializer.data)

#     def post(self, request, format=None):
#         # request.data gets somethig from outside and serializer turns it into a pythn type.
#         serializer = KollegeSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class KollegeDetail(generics.RetrieveUpdateDestroyAPIView):

#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'home.html'

#     queryset = Kollege.objects.all()
#     serializer_class = KollegeSerializer

#     permission_classes =[permissions.IsAuthenticatedOrReadOnly,]

#     # Override:
#     def get_object(self, pk):
#         try:
#             return Kollege.objects.get(pk=pk)
#         except Kollege.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         kollege = self.get_object(pk)
#         serializer = KollegeSerializer(kollege)
#         # Code (a dict) necessery to renser the template.
#         # Error if not:context must be a dict rather than ReturnList.
#         #return Response({'serializer': serializer, 'kollege': kollege})
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         kollege = self.get_object(pk)
#         serializer = KollegeSerializer(kollege, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         kollege = self.get_object(pk)
#         kollege.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class PersonaList(generics.ListCreateAPIView):

#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'inicio.html'

#     permission_classes = [permissions.IsAuthenticatedOrReadOnly,]

#     queryset = Persona.objects.all()
#     serializer_class = PersonaSerializer

#     # Override: for the view to render on the homexxx.html, the template_name
#     # and the renderer_classes must be set. Also, the get and post methods
#     # must be overriden.
#     def get(self, request, format=None):
#         # gets a queryset
#         personas = Persona.objects.all()
#         # gets a python type (dict)
#         serializer = PersonaSerializer(personas, many=True)
#         # if request.path_info == '/api/persona/inicio/':
#         #     return Response({'serializer': serializer, 'personas': personas}, template_name='inicio.html')
#         # elif request.path_info == '/api/persona/calender/':
#         #     return Response({'serializer': serializer, 'personas': personas}, template_name='calender.html')
#         return Response({'serializer': serializer, 'personas': personas})
#         #return Response(serializer.data)

#     def post(self, request, format=None):
#         # request.data gets somethig from outside and serializer turns it into a pythn type.
#         serializer = PersonaSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class PersonaDetail(generics.RetrieveUpdateDestroyAPIView):

#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'home.html'

#     queryset = Persona.objects.all()
#     serializer_class = PersonaSerializer

#     permission_classes =[permissions.IsAuthenticatedOrReadOnly,]

#     # Override:
#     def get_object(self, pk):
#         try:
#             return Persona.objects.get(pk=pk)
#         except Persona.DoesNotExist:
#             raise Http404

#     def get(self, request, pk, format=None):
#         persona = self.get_object(pk)
#         serializer = PersonaSerializer(persona)
#         # Code (a dict) necessery to renser the template.
#         # Error if not:context must be a dict rather than ReturnList.
#         #return Response({'serializer': serializer, 'persona': persona})
#         return Response(serializer.data)

#     def put(self, request, pk, format=None):
#         persona = self.get_object(pk)
#         serializer = PersonaSerializer(persona, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         persona = self.get_object(pk)
#         persona.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# #class EventList(generics.ListCreateAPIView):
# class EventList(mixins.RetrieveModelMixin,
#                     mixins.UpdateModelMixin,
#                     mixins.DestroyModelMixin,
#                     generics.GenericAPIView):

#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'calender.html'

#     permission_classes = [permissions.IsAuthenticatedOrReadOnly,]

#     #queryset = Event.objects.all()
#     #serializer_class = EventSerializer

#     # Override: for the view to render on the homexxx.html, the template_name
#     # and the renderer_classes must be set. Also, the get and post methods
#     # must be overriden.
#     def get(self, request, format=None):
#         # gets a queryset
#         events = Event.objects.all()
#         # gets a python type (dict)
#         serializer = EventSerializer(events, many=True)
#         return Response({'serializer': serializer,
#                          'events': events})
#         #return Response(serializer.data)

#     ####### https://www.django-rest-framework.org/topics/html-and-forms/ ######
#     def post(self, request, format=None):
#         #events = Event.objects.all()
#         # QueryDict is immutable:
#         # user = self.request.user
#         # request.data gets somethig from outside and serializer turns it into a pythn type.
#         serializer = EventSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response({ 'serializer': serializer})
# #            return Response({'serializer': serializer},
# #                              status=status.HTTP_201_CREATED,
# #                              )
#         serializer.save()
#         return redirect('event-list')
#         #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# '''
#     renderer_classes = [TemplateHTMLRenderer]
#     #template_name = 'calender.html'

#     permission_classes = [permissions.IsAuthenticatedOrReadOnly,]

#     queryset = Event.objects.all()
#     #serializer_class = EventSerializer

#     # Override: for the view to render on the homexxx.html, the template_name
#     # and the renderer_classes must be set. Also, the get and post methods
#     # must be overriden.
#     def get(self, request, format=None):
#         # gets a queryset
#         events = Event.objects.all()
#         personas = Persona.objects.all()
#         kollegen = Kollege.objects.all()
#         # gets a python type (dict)
#         serializer1 = EventSerializer(events, many=True)
#         serializer2 = PersonaSerializer(personas, many=True)
#         serializer3 = KollegeSerializer(kollegen, many=True)
#         if request.path_info == '/api/persona/inicio/':
#             return Response({'serializer1': serializer1,
#                              'serializer2': serializer2,
#                              'events': events,
#                              'personas': personas},
#                              template_name='inicio.html')
#         elif request.path_info == '/api/persona/calender/':
#             return Response({'serializer1': serializer1,
#                              'serializer2': serializer2,
#                              'serializer3': serializer3,
#                              'events': events,
#                              'personas': personas,
#                              'kollegen': kollegen},
#                              template_name='calender.html')
#         #return Response(serializer.data)

#     def post(self, request, format=None):
#         # QueryDict is immutable:
#         # user = self.request.user
#         print(request.data['user'])
#         # request.data gets somethig from outside and serializer turns it into a pythn type.
#         serializer = EventSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, template_name = 'calender.html', status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, template_name = 'error.html', status=status.HTTP_400_BAD_REQUEST)
# '''

# #class EventDetail(generics.RetrieveUpdateDestroyAPIView):
# class EventDetail(mixins.RetrieveModelMixin,
#                     mixins.UpdateModelMixin,
#                     mixins.DestroyModelMixin,
#                     generics.GenericAPIView):


#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'event-detail.html'

#     #queryset = Event.objects.all()
#     #serializer_class = EventSerializer

#     permission_classes =[permissions.IsAuthenticatedOrReadOnly,]

#     # Override:
#     def get_object(self, pk):
#         try:
#             return Event.objects.get(pk=pk)
#         except Event.DoesNotExist:
#             raise Http404

#     # Working
#     def get(self, request, pk, format=None):
#         event = self.get_object(pk)
#         serializer = EventSerializer(event)
#         # Code (a dict) necessery to renser the template.
#         # Error if not:context must be a dict rather than ReturnList.
#         return Response({'serializer': serializer, 'event': event})
#         # This was not comentted and the error was:
#         # Reverse for 'event-detail' with keyword arguments '{'pk': ''}' not found
#         #return Response(serializer.data)

#     # Working
#     def post(self, request, pk):
#         event = get_object_or_404(Event, pk=pk)
#         serializer = EventSerializer(event, data=request.data)
#         if not serializer.is_valid():
#             return Response({'serializer': serializer, 'event': event})
#         serializer.save()
#         return redirect('event-list')

#     def put(self, request, pk, format=None):
#         event = self.get_object(pk)
#         serializer = EventSerializer(event, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk, format=None):
#         event = self.get_object(pk)
#         Event.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# '''

# from rest_framework import viewsets, mixins
# from rest_framework.response import Response
# from rest_framework.authentication import TokenAuthentication
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

# from persona.serializers import KollegeSerializer

# from django.shortcuts import render
# import requests

# from core.models import Kollege, Event, Persona

# from persona import serializers


# class BasePersonaAttrViewSet(viewsets.GenericViewSet,
#                              mixins.ListModelMixin,
#                              mixins.CreateModelMixin,
#                              mixins.RetrieveModelMixin,
#                              mixins.DestroyModelMixin,
#                              mixins.UpdateModelMixin):
#     """Base viewset for user owned persona attr"""
#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)

#     def perform_create(self, serializer):
#         """Create a new object"""
#         serializer.save(user=self.request.user)


# # Gone use only list mixin. There are update, delete mixins ...
# class KollegeViewSet(BasePersonaAttrViewSet):
#     """Manage kollegen in the db"""
#     renderer_classes = [TemplateHTMLRenderer]
#     template_name = 'home.html'

#     # ListModeMixin requires a queryset set
#     queryset = Kollege.objects.all()
#     serializer_class = serializers.KollegeSerializer

#     def get_queryset(self):
#         """Return objects for current auth user only"""
#         return self.queryset.filter(user=self.request.user).order_by('-name')

#     def get(self, format=None):
#         # gets a queryset
#         kollegen = Kollege.objects.all()
#         # gets a python type (dict)
#         serializer = KollegeSerializer(kollegen, many=True)
#         return Response({'serializer': serializer, 'kollegen': kollegen})
#         #return Response(serializer.data)

#     def post(self, request, format=None):
#         # request.data gets somethig from outside and serializer turns it into a pythn type.
#         serializer = KollegeSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class EventViewSet(BasePersonaAttrViewSet):
#     """Manage events in the db"""
#     queryset = Event.objects.all()
#     serializer_class = serializers.EventSerializer

#     def get_queryset(self):
#         """Return objects for the current authenticated user"""
#         return self.queryset.filter(user=self.request.user).order_by('title')


# # Gonna implement more functionalities here not only list
# class PersonaViewSet(viewsets.ModelViewSet):
#     """Manage persona in the db"""
#     serializer_class = serializers.PersonaSerializer
#     queryset = Persona.objects.all()
#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)

#     def get_queryset(self):
#         """Retrieve the personas for the auth user"""
#         return self.queryset.filter(user=self.request.user).order_by('name')

#     # Called to retrieve the serializer_class for a particular request.
#     # Useful to change the default (list) action of the serializer_class.
#     def get_serializer_class(self):
#         """Return appropriate serializer class"""
#         # The action 'retrieve' needs a detail serializer. Know it is retrieve
#         # if api/persona/personas/<anything>
#         if self.action == 'retrieve':
#             return serializers.PersonaDetailSerializer

#         return self.serializer_class

#     def perform_create(self, serializer):
#         """Create a new persona and assign the user of the persona to the
#         current user"""
#         serializer.save(user=self.request.user)
# '''
