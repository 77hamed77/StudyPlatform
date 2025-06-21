# news/templatetags/news_extras.py
from django import template
register = template.Library()

@register.filter
def find_field_label(form, field_name):
    if field_name == '__all__':
        return '' # لا يوجد تسمية لـ non_field_errors
    if field_name in form.fields:
        return form.fields[field_name].label
    return field_name.replace('_', ' ').capitalize() # محاولة تخمين التسمية