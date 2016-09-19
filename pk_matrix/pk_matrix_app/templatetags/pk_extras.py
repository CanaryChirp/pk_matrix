from django import template

register = template.Library()

@register.filter('conjug')
def conjug(name):
	if name == 'You':
		return ''
	else:
		return 's'