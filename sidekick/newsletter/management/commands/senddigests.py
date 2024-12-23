from django.core.management.base import BaseCommand
from sidekick.newsletter.models import Subscriber


class Command(BaseCommand):
    help = 'Send newsletter digests to subscribers.'

    def handle(self, *args, **options):
        for subscriber in Subscriber.objects.filter(
            status__iexact='subscribed'
        ).iterator():
            subscriber.send_digest()
