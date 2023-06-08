from django import template

register = template.Library()

@register.simple_tag
def pluralize_reviews(count):
    if count == 1:
        return f"{count} отзыв"
    elif 2 <= count <= 4:
        return f"{count} отзыва"
    else:
        return f"{count} отзывов"