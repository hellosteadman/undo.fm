from django.conf import settings
from django.db.models import Manager
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from sidekick.contrib.notion import sync as notion_sync
from sidekick.mail import render_to_inbox
import jwt


class PostManager(Manager):
    def sync(self):
        def clean(obj, doc):
            if not obj.slug:
                obj.slug = slugify(obj.title)

            if not obj.status:
                obj.status = 'draft'

        return notion_sync.to_model(
            self.model,
            before_clean=clean,
            blocks_field='content',
            media_handler='attach'
        )


class SubscriberManager(Manager):
    def send_confirmation(self, email, name='', excluded_tags=[]):
        first_name = 'there'
        if name:
            first_name = name.split()[0].capitalize()

        token = jwt.encode(
            {
                'eml': email,
                'name': name,
                'exc': list(
                    excluded_tags.values_list('pk', flat=True)
                ),
                'exp': timezone.now() + timezone.timedelta(days=1)
            },
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        confirm_url = 'http%s://%s%s' % (
            not settings.DEBUG and 's' or '',
            settings.DOMAIN,
            reverse('confirm_subscriber', args=(token,))
        )

        render_to_inbox(
            (name, email),
            'Ready to get Undo in your inbox?',
            'newsletter/confirm_email.html',
            {
                'name': first_name,
                'confirm_url': confirm_url
            },
            'Please confirm your intention to subscribe.'
        )

    def sync(self):
        def clean(obj, doc):
            obj.subscribed = doc['created_time']

        return notion_sync.to_model(
            self.model,
            before_clean=clean
        )
