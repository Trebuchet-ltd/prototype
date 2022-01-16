from django import template

register = template.Library()


@register.simple_tag()
def multiply(*numbers):
    no = 1
    for n in numbers:
        no *= n

    return no


@register.simple_tag()
def name_of(item):
    return f"{item.item.title}-Cleaned" if item.is_cleaned else item.item.title


@register.simple_tag()
def code_of(item):
    return f"*{item.item.code}" if item.is_cleaned else item.item.code


@register.simple_tag()
def quantity_of(item):
    return item.quantity * item.item.weight


@register.simple_tag()
def price_of(item):
    return item.quantity * item.price * item.item.weight * (item.item.product_gst_percentage/100.0 + 1)


@register.simple_tag()
def string(field):
    return str(field)
