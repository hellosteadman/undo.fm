from django.contrib.syndication.views import Feed
from django.utils import feedgenerator, timezone
from .models import Post


class ContenetEncodedRss201rev2Feed(feedgenerator.Rss201rev2Feed):
    def root_attributes(self):
        attrs = super().root_attributes()
        attrs['xmlns:content'] = 'http://purl.org/rss/1.0/modules/content/'
        return attrs
        
    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        handler.addQuickElement('content:encoded', item['content_encoded'])


class PostFeed(Feed):
    feed_type = ContenetEncodedRss201rev2Feed
    title = 'Undo'
    link = 'https://undo.fm/posts/'
    description = 'Tips and templates to help you get the most out of Notion.'
    author_name = 'Mark Steadman'
    item_author_name = 'Mark Steadman'
    item_guid_is_permalink = True

    def feed_copyright(self):
        return 'Copyright ©️ %d Hello Steadman Ltd' % timezone.now().year

    def items(self):
        return Post.objects.filter(
            published__lte=timezone.now(),
            status__iexact='published'
        )

    def item_description(self, obj):
        return obj.get_excerpt()

    def item_content_encoded(self, obj):
        return obj.content.render(simple=True)

    def item_extra_kwargs(self, obj):
        return {
            'content_encoded': self.item_content_encoded(obj)
        }

    def item_pubdate(slef, obj):
        return obj.published
