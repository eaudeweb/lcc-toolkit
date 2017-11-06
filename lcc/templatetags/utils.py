from django import template
register = template.Library()


@register.filter(name='index')
def index(items, i):
    return items[int(i)]


@register.simple_tag(takes_context=True)
def active(context, *args):
    if set(context['request'].resolver_match.namespaces).issubset(args):
        return 'active'
    return ''
