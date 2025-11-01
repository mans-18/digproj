import threading
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from core.models import Persona, Event, Kollege


CC_EMAIL = "digest.principal@gmail.com"


def send_email(kol):
    """Send tomorrow's schedule email for one colleague."""
    tomorrow = date.today() + timedelta(days=1)
    if tomorrow.weekday() == 5:  # Saturday
        print("⏩ Skipping Saturday")
        return

    events = (
        Event.objects.filter(start__date=tomorrow, kollege_id=kol['id'])
        .select_related('persona')
        .order_by('start')
    )

    if not events.exists():
        print(f"⚠️ No events found for {kol['name']}")
        return

    # Build event/persona data
    persona_data = [
        {"name": ev.persona.name, "start": ev.start, "title": ev.title, "color": getattr(ev, 'color', '')}
        for ev in events
    ]

    context = {
        "event_data": events,
        "persona_data": persona_data,
        "kollege_id": kol['id'],
        "extra": kol['name'],
        "toEmailCount": 1,
    }

    msg_html = render_to_string("email2.html", context)

    subject = f"Agenda de amanhã - {kol['name']}"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@digest.com")
    to_email = [kol['email']]
    cc_email = [CC_EMAIL]

    # ✅ Proper CC handling
    email = EmailMultiAlternatives(
        subject=subject,
        body="Segue sua agenda de amanhã.",
        from_email=from_email,
        to=to_email,
        cc=cc_email,
    )
    email.attach_alternative(msg_html, "text/html")

    try:
        email.send(fail_silently=False)
        print(f"✅ Sent to {kol['email']} (CC {CC_EMAIL})")
    except Exception as e:
        print(f"❌ Failed to send email to {kol['email']}: {e}")


class Command(BaseCommand):
    help = "Send daily kollege emails (except Saturday) with CC to digest.principal@gmail.com."

    def handle(self, *args, **options):
        tomorrow = date.today() + timedelta(days=1)

        # Skip Saturdays
        if tomorrow.weekday() == 5:
            self.stdout.write("Saturday: skipping emails.")
            return

        # Get all colleagues with events tomorrow
        kollege_ids = (
            Event.objects.filter(start__date=tomorrow)
            .values_list('kollege_id', flat=True)
            .distinct()
        )
        kollege_ids = set(Event.objects.filter(start__date=tomorrow).values_list('kollege_id', flat=True))
        kollege_list = []
        for kol_id in kollege_ids:
            try:
                kol = Kollege.objects.get(id=kol_id)
                if kol.email:
                    kollege_list.append({"id": kol.id, "name": kol.name, "email": kol.email})
            except Kollege.DoesNotExist:
                continue

        if not kollege_list:
            self.stdout.write("⚠️ No colleagues found with events for tomorrow.")
            return

        # Send emails in parallel threads
        threads = []
        for kol in kollege_list:
            t = threading.Thread(target=send_email, args=(kol,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        self.stdout.write(self.style.SUCCESS(f"✅ Sent emails to {len(kollege_list)} colleagues (CC {CC_EMAIL})."))




'''
# NO THREADING
# WITH TIMEZONE. BUT THE BACKEND DO NOT USE (?) SO THE TIME IS AHEAD
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from core.models import Kollege, Event, Persona

CC_EMAIL = "digest.principal@gmail.com"

class Command(BaseCommand):
    help = "Send daily email summaries to colleagues with tomorrow's events (except Saturday)."

    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + timedelta(days=1)

        # Skip Saturday
        if tomorrow.weekday() == 5:
            self.stdout.write("⏭️ Saturday detected — skipping email send.")
            return

        # Get all colleagues who have events tomorrow
        kolleges = (
            Kollege.objects.filter(event_kollege__start__date=tomorrow)
            .distinct()
            .prefetch_related("event_kollege__persona")
        )

        sent_count = 0

        for kollege in kolleges:
            events = kollege.event_kollege.filter(start__date=tomorrow).select_related("persona")

            if not events.exists():
                continue

            subject = f"Agenda de amanhã - {kollege.name}"
            message_lines = [f"Olá {kollege.name},", "", "Segue sua agenda de amanhã:\n"]

            for ev in events:
                message_lines.append(
                    f"• {ev.persona.name} — {ev.title} às {ev.start.strftime('%H:%M')}"
                )

            message_lines.append("\nAtenciosamente,\nEquipe Digest")
            message = "\n".join(message_lines)

            try:
                send_mail(
                    subject,
                    message,
                    CC_EMAIL,  # from email
                    [kollege.email],
                    fail_silently=False,
                    html_message=None,
                )
                # CC handling (send_mail does not have a CC param directly)
                send_mail(
                    subject,
                    message,
                    CC_EMAIL,
                    [CC_EMAIL],  # Send copy
                    fail_silently=True,
                )
                self.stdout.write(f"✅ Email sent to {kollege.email}")
                sent_count += 1
            except Exception as e:
                self.stdout.write(f"❌ Failed to send to {kollege.email}: {e}")

        self.stdout.write(f"📨 Sent {sent_count} email(s).")
'''