from django import template

register = template.Library()

@register.filter(name='split')
def split_filter(value, delimiter=','):
    if value:
        return [item.strip() for item in str(value).split(delimiter)]
    return [] 