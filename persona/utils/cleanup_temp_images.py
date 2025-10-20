from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import TemporaryImage

class Command(BaseCommand):
    help = "Delete TemporaryImage older than X hours"

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        old = TemporaryImage.objects.filter(uploaded_at__lt=cutoff)
        count = old.count()
        for t in old:
            t.image.delete(save=False)
            t.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} temporary images older than {options['hours']} hours"))
