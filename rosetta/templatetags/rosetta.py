from django import template
from django.template.loader_tags import do_include
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re
import six

from rosetta.access import can_translate


register = template.Library()
rx = re.compile(r'(%(\([^\s\)]*\))?[sd]|\{[\w\d_]+?\})')

can_translate = register.filter(can_translate)


def format_message(message):
    return mark_safe(rx.sub('<code>\\1</code>', escape(message).replace(r'\n', '<br />\n')))
format_message = register.filter(format_message)


def lines_count(message):
    return 1 + sum([len(line) / 50 for line in message.split('\n')])
lines_count = register.filter(lines_count)


def mult(a, b):
    return int(a) * int(b)
mult = register.filter(mult)


def minus(a, b):
    try:
        return int(a) - int(b)
    except:
        return 0
minus = register.filter(minus)


def gt(a, b):
    try:
        return int(a) > int(b)
    except:
        return False
gt = register.filter(gt)


def do_incr(parser, token):
    args = token.split_contents()
    if len(args) < 2:
        raise SyntaxError("'incr' tag requires at least one argument")
    name = args[1]
    if not hasattr(parser, '_namedIncrNodes'):
        parser._namedIncrNodes = {}
    if name not in parser._namedIncrNodes:
        parser._namedIncrNodes[name] = IncrNode(0)
    return parser._namedIncrNodes[name]
do_incr = register.tag('increment', do_incr)


class IncrNode(template.Node):
    def __init__(self, init_val=0):
        self.val = init_val

    def render(self, context):
        self.val += 1
        return six.text_type(self.val)


def is_fuzzy(message):
    return message and hasattr(message, 'flags') and 'fuzzy' in message.flags
is_fuzzy = register.filter(is_fuzzy)


def template_exists(template_name):
    try:
        get_template(template_name)
        return True
    except template.TemplateDoesNotExist:
        return 
template_exists = register.filter(template_exists)


class TryIncludeNode(template.Node):
    """
    A Node that instantiates an IncludeNode but wraps its render() in a
    try/except in case the template doesn't exist.
    """
    def __init__(self, parser, token):
        self.include_node = do_include(parser, token)

    def render(self, context):
        try:
            return self.include_node.render(context)
        except template.TemplateDoesNotExist:
            return ''


@register.tag('try_include')
def try_include(parser, token):
    """
    Include the specified template but only if it exists.
    """
    return TryIncludeNode(parser, token)