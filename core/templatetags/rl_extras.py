from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def stars(value):
    """Turn a rating such as 4.5 into 5 star icons (full, half, empty)."""
    try:
        rating = float(value or 0)
    except (TypeError, ValueError):
        rating = 0
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half
    html = (
        '<i class="bi bi-star-fill"></i>' * full
        + '<i class="bi bi-star-half"></i>' * half
        + '<i class="bi bi-star"></i>' * empty
    )
    # Safe: the HTML above is built only from our own constant strings.
    return mark_safe(f'<span class="rl-stars">{html}</span>')