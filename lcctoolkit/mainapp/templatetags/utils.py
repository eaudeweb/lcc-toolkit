from django import template
register = template.Library()


@register.filter(name='index')
def index(List, i):
    return List[int(i)]
