from django import template
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.template.loader import render_to_string

from genesishealth.apps.utils.views import get_action_icon, ActionIconException

register = template.Library()


def parse_and_get_context_variable(context, token):
    token_split = token.split('.')
    obj = context[token_split[0]]
    for i in token_split[1:]:
        if isinstance(obj, dict):
            obj = obj[i]
        else:
            obj = getattr(obj, i)
        if callable(obj):
            obj = obj.__call__()
    return obj


class GetDashboardURLNode(template.Node):
    def __init__(self, view_name, tag_args):
        self.view_name = view_name
        self.tag_args = tag_args

    def render(self, context):
        reverse_args = []
        for ta in self.tag_args:
            if ((ta.startswith("'") and ta.endswith("'")) or
                    (ta.startswith('"') and ta.endswith('"'))):
                reverse_args.append(ta)
            else:
                try:
                    reverse_args.append(
                        parse_and_get_context_variable(context, ta))
                except Exception:
                    raise template.TemplateSyntaxError(
                        "%s is an invalid template variable" % ta)
        try:
            reverse_url = reverse(self.view_name, args=reverse_args)
        except NoReverseMatch:
            raise template.TemplateSyntaxError(
                "%s did not match a configured URL with the provided"
                " parameters: %s" % (self.view_name, reverse_args))
        return "%s%s" % (settings.DASHBOARD_PREFIX, reverse_url)


@register.tag(name='get_dashboard_url')
def do_get_dashboard_url(parser, token):
    try:
        contents = token.split_contents()
        tag_name, view_name = contents[:2]
        args = contents[2:]

    except ValueError:
        raise template.TemplateSyntaxError(
            "%r requires at least one argument: view_name"
            % token.contents.split()[0])

    return GetDashboardURLNode(view_name, args)


class DisplaySystemMessagesNode(template.Node):
    def render(self, context):
        try:
            assert context.get('request') is not None
            assert hasattr(context.get('request'), 'session') is not None
            assert context['request'].session.get(
                'system_messages') is not None
        except AssertionError:
            return ''

        return render_to_string(
            'utils/system_message.html',
            {'messages': context.get('request').session.pop(
                'system_messages')})


@register.tag(name='display_system_messages')
def do_display_system_messages(parser, token):
    return DisplaySystemMessagesNode()


class GetActionIconClassNode(template.Node):
    def __init__(self, view_name):
        self.view_name = template.Variable(view_name)

    def render(self, context):
        try:
            return get_action_icon(self.view_name.resolve(context))
        except (ActionIconException, template.VariableDoesNotExist):
            return settings.TABLE_ACTION_ICON_CLASSES.get('default')


@register.tag(name='get_action_icon_class')
def do_get_action_icon_class(parser, token):
    tag_name, view_name = token.split_contents()
    return GetActionIconClassNode(view_name)


class IfSettingNode(template.Node):
    def __init__(self, nodelist, setting_name):
        self.setting_name = setting_name
        self.nodelist = nodelist

    def render(self, context):
        if getattr(settings, self.setting_name):
            return self.nodelist.render(context)
        return ''


@register.tag(name='if_setting')
def do_if_setting_node(parser, token):
    tag_name, setting_name = token.split_contents()

    nodelist = parser.parse(('end_if_setting',))
    parser.delete_first_token()

    return IfSettingNode(nodelist, setting_name)


class IfSettingEqualsNode(template.Node):
    def __init__(self, nodelist, setting_name, equal_value):
        self.setting_name = setting_name
        self.equal_value = equal_value
        self.nodelist = nodelist

    def render(self, context):
        if getattr(settings, self.setting_name) == self.equal_value:
            return self.nodelist.render(context)
        return ''


@register.tag(name='if_setting_equals')
def do_if_setting_equal_node(parser, token):
    tag_name, setting_name, equal_value = token.split_contents()

    nodelist = parser.parse(('end_if_setting_equals',))
    parser.delete_first_token()

    return IfSettingEqualsNode(nodelist, setting_name, equal_value)
