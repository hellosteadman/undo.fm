from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.http.response import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    View,
    ListView,
    DetailView,
    FormView,
    UpdateView,
    TemplateView
)

from easy_thumbnails.files import get_thumbnailer
from hashlib import md5
from sidekick.contrib.notion import sync
from sidekick.seo.views import (
    SEOMixin,
    OpenGraphMixin,
    OpenGraphArticleMixin,
    LinkedDataMixin
)

from taggit.models import Tag
from urllib.parse import urlencode
from .forms import SubscriberForm
from .models import Post, Subscriber
import jwt


class PostMixin(SEOMixin, LinkedDataMixin):
    model = Post
    ld_type = 'BlogPost'


class PostListView(PostMixin, OpenGraphMixin, ListView):
    paginate_by = 24
    og_title = 'Post archive'
    og_description = (
        'Spend your time reading about productivity and avoid getting '
        'anything done.'
    )

    ld_type = 'Blog'
    ld_attributes = {
        'name': 'Undo'
    }

    def get_tags(self):
        if not hasattr(self, '_tags'):
            slugs = self.request.GET.getlist('tag')
            self._tags = Tag.objects.none()

            if any(slugs):
                self._tags = Tag.objects.filter(
                    slug__in=slugs
                ).distinct()

        return self._tags

    def get_author(self):
        if not hasattr(self, '_author'):
            self._author = None

            if username := self.request.GET.get('author'):
                self._author = User.objects.filter(
                    username=username
                ).first()

        return self._author

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            published__lte=timezone.now(),
            status__iexact='published'
        )

        if tags := self.get_tags():
            queryset = queryset.filter(
                tags__in=tags
            )

        if author := self.get_author():
            queryset = queryset.filter(
                author=author
            )

        return queryset.distinct()

    def get_seo_title(self):
        title = 'Undo blog'

        if tags := self.get_tags():
            title += ' tagged %s' % ', '.join(
                [tag.name for tag in tags]
            )

        if author := self.get_author():
            title += ' by %s' % author.get_full_name()

        return title

    def get_context_data(self, **kwargs):
        tags = kwargs.get('tags', self.get_tags())
        user = kwargs.get('user', self.get_author())

        return {
            **super().get_context_data(**kwargs),
            'tags': tags,
            'author': user
        }


class PostDetailView(PostMixin, OpenGraphArticleMixin, DetailView):
    ld_type = 'BlogPosting'
    ld_breadcrumbs = [
        ('/', 'Home'),
        ('../', 'Archive'),
        ('.', '__str__')
    ]

    def get_og_description(self):
        return self.get_object().get_excerpt()
    
    def get_ld_attributes(self):
        obj = self.get_object()
        word_count = obj.content.aggregate(
            count=Sum('word_count')
        )

        attrs = {
            'headline': obj.title,
            'inLanguage': 'en-gb',
            'url': self.request.build_absolute_uri(
                reverse('post_list')
            ),
            'description': obj.get_excerpt(),
            'keywords': obj.tags.values_list('name', flat=True),
            'author': {
                '@type': 'Person',
                'name': obj.author.get_full_name(),
                'givenName': obj.author.first_name,
                'familyName': obj.author.last_name,
                'image': {
                    '@type': 'imageObject',
                    'url': 'https://secure.gravatar.com/avatar/%s?%s' % (
                        md5(obj.author.email.encode('utf-8')).hexdigest(),
                        urlencode(
                            {
                                's': 400,
                                'd': 'mp',
                                'r': 'g'
                            }
                        )
                    ),
                    'width': 400,
                    'height': 400
                }
            },
            'publisher': {
                '@type': 'WebSite',
                'name': 'Undo',
                'url': self.request.build_absolute_uri('/')
            }
        }

        if word_count and word_count.get('count'):
            attrs['wordCount'] = word_count['count']

        if obj.published:
            attrs['datePublished'] = obj.published

        if img_block := obj.content.filter(type='image').first():
            if img_block.ordering == 0 or img_block.ordering == 1:
                src = img_block.properties['src']
                thumbnailer = get_thumbnailer(src)

                if thumb := thumbnailer.get_thumbnail(
                    {
                        'size': (1200, 630),
                        'crop': True
                    }
                ):
                    attrs['image'] = {
                        '@type': 'ImageObject',
                        'url': thumb.url,
                        'width': thumb.width,
                        'height': thumb.height
                    }

        return attrs

    def get_context_data(self, **kwargs):
        return {
            'subscribe_form': SubscriberForm(),
            'webmention_url': self.request.build_absolute_uri(
                reverse('webmention:receive')
            ),
            **super().get_context_data(**kwargs)
        }


class CreateSubscriberView(SEOMixin, FormView):
    template_name = 'newsletter/subscriber_form.html'
    form_class = SubscriberForm
    seo_title = 'Subscribe to the Undo newsletter'

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('subscriber_created')


class SubscriberCreatedView(SEOMixin, TemplateView):
    robots = 'noindex'
    template_name = 'newsletter/subscriber_created.html'


class ConfirmSubscriberView(View):
    def get_object(self):
        token = jwt.decode(
            self.kwargs['token'],
            settings.SECRET_KEY,
            algorithms=('HS256',)
        )

        obj, created = Subscriber.objects.get_or_create(
            email__iexact=token['eml'],
            defaults={
                'email': token['eml'],
                'name': token['name'],
                'subscribed': timezone.now(),
                'status': 'Subscribed'
            }
        )

        excluded_tags = Tag.objects.filter(
            pk__in=token['exc']
        )

        obj.excluded_tags.add(*excluded_tags)
        obj.notion_id = sync.from_model(obj)
        obj.save()

        return obj

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except jwt.InvalidTokenError:
            return TemplateResponse(
                self.request,
                'newsletter/invalid_token.html',
                status=400
            )

        return HttpResponseRedirect(
            '%s?id=%s' % (
                self.get_success_url(),
                obj.notion_id
            )
        )

    def get_success_url(self):
        return reverse('subscriber_confirmed')


class SubscriberConfirmedView(SEOMixin, TemplateView):
    robots = 'noindex'
    seo_title = 'Subscription confirmed'
    template_name = 'newsletter/subscriber_confirmed.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if notion_id := self.request.GET.get('id'):
            ctx['object'] = Subscriber.objects.filter(
                notion_id=notion_id
            ).first()

        return ctx


class UpdateSubscriberView(SEOMixin, UpdateView):
    robots = 'noindex'
    form_class = SubscriberForm
    
    def get_seo_title(self):
        return 'Update your email preferences'

    def get_object(self):
        token = jwt.decode(
            self.kwargs['token'],
            settings.SECRET_KEY,
            algorithms=('HS256',)
        )

        try:
            return Subscriber.objects.get(
                notion_id=token['n']
            )
        except Subscriber.DoesNotExist:
            raise Http404('Subscriber not found.')

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except jwt.InvalidTokenError:
            return TemplateResponse(
                self.request,
                'newsletter/invalid_token.html',
                status=400
            )

    def get_success_url(self):
        return reverse('subscriber_updated')


class SubscriberUpdatedView(SEOMixin, TemplateView):
    robots = 'noindex'
    seo_title = 'Details updated'
    template_name = 'newsletter/subscriber_updated.html'


class UnsubscribeView(SEOMixin, View):
    robots = 'noindex'

    def get_object(self):
        token = jwt.decode(
            self.kwargs['token'],
            settings.SECRET_KEY,
            algorithms=('HS256',)
        )

        try:
            return Subscriber.objects.get(
                notion_id=token['n']
            )
        except Subscriber.DoesNotExist:
            raise Http404('Subscriber not found.')

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except jwt.InvalidTokenError:
            return TemplateResponse(
                self.request,
                'newsletter/invalid_token.html',
                status=400
            )

        if request.method == 'GET':
            obj.status = 'Unsubscribed'
            obj.save()
            sync.from_model(obj)

        return HttpResponseRedirect(
            self.get_success_url()
        )

    def get_success_url(self):
        return reverse('unsubscribed')


class UnsubscribedView(SEOMixin, TemplateView):
    robots = 'noindex'
    seo_title = 'Unsubscribed'
    template_name = 'newsletter/unsubscribed.html'


class EmailPreview(ListView):
    model = Post
    paginate_by = 5
    template_name = 'newsletter/digest_email.html'
