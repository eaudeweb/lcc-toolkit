from django import template
register = template.Library()


@register.filter(name='index')
def index(items, i):
    return items[int(i)]
