from django import template
register = template.Library()


@register.filter(name='index')
def index(items, i):
    return items[int(i)]


@register.simple_tag(takes_context=True)
def active(context, *args):
    resolver = context['request'].resolver_match
    if resolver.url_name == 'about_us':
        return ''

    if set(resolver.namespaces).issubset(args):
        return 'active'
    return ''
