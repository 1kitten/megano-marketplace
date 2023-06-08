from django import template

register = template.Library()

@register.simple_tag
def get_range(value):
    return range(value)