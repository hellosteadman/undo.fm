from django.contrib.staticfiles.storage import staticfiles_storage as static
from django.utils import timezone
from django.views.generic import TemplateView, DetailView
from easy_thumbnails.files import get_thumbnailer
from sidekick.newsletter.forms import SubscriberForm
from sidekick.newsletter.models import Post
from sidekick.seo.views import (
    SEOMixin,
    OpenGraphMixin,
    OpenGraphArticleMixin,
    LinkedDataMixin
)

from .models import Page


class IndexView(SEOMixin, OpenGraphMixin, LinkedDataMixin, TemplateView):
    template_name = 'front/index.html'
    seo_title = 'Undo'
    seo_description = 'A podcast history of productivity'
    og_type = 'website'
    og_title = 'Undo'
    og_description = (
        'The podcast exploring how history’s outliers got stuff done'
    )

    ld_type = 'WebSite'
    ld_attributes = {
        'name': 'Undo',
        'description': (
            'An examination into how history’s oddballs, outliers, '
            'and overachievers built systems to help them do their '
            'best work.'
        ),
        'publisher': {
            '@type': 'Person',
            'name': 'Mark Steadman',
            'givenName': 'Mark',
            'familyName': 'Steadman',
            'url': 'https://hellosteadman.com/',
            'image': {
                '@type': 'ImageObject',
                'url': static.url('img/mark.jpg'),
                'width': 400,
                'height': 400
            },
            'contactPoint': {
                '@type': 'ContactPoint',
                'email': 'editor@undo.fm',
                'url': 'https://hellosteadman.com/',
                'contactType': 'customer service'
            },
            'sameAs': [
                'https://mastodon.social/@hellosteadman',
                'https://www.linkedin.com/in/hellosteadman/',
                'https://www.instagram.com/hellosteadman/',
                'https://www.threads.net/@hellosteadman/'
            ]
        },
        'logo': {
            '@type': 'ImageObject',
            'url': static.url('img/logo.png')
        },
        'copyrightNotice': '© Hello Steadman Ltd',
        'copyrightYear': '2024',
        'locationCreated': {
            '@type': 'Place',
            'address': {
                '@type': 'PostalAddress',
                'addressLocality': 'Birmingham',
                'addressCountry': 'GB'
            }
        }
    }

    def get_context_data(self, **kwargs):
        posts = kwargs.get(
            'posts',
            Post.objects.filter(
                published__lte=timezone.now(),
                status__iexact='published'
            )[:12]
        )

        return {
            **super().get_context_data(**kwargs),
            'form': kwargs.get('form', SubscriberForm()),
            'post_list': posts
        }


class PageDetailView(
    SEOMixin, LinkedDataMixin, OpenGraphArticleMixin, DetailView
):
    model = Page
    ld_type = 'WebPage'

    def get_og_description(self):
        return self.get_object().get_excerpt()

    def get_ld_attributes(self):
        obj = self.get_object()
        attrs = {
            'headline': obj.title,
            'inLanguage': 'en-gb',
            'url': self.request.build_absolute_uri(
                obj.get_absolute_url()
            ),
            'description': obj.get_excerpt()
        }

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
