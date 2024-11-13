from django.template import Library

register = Library()

@register.filter
def to_int(value):
    return int(value)

@register.filter
def int_for_loop(value):
    return map(int, value.split())