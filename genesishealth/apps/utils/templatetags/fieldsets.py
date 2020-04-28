from collections import OrderedDict
import copy

from django import template

register = template.Library()


def get_fieldset(parser, token):
    try:
        name, fields, as_, variable_name, from_, form = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            'bad arguments for {}'.format(
                token.split_contents()[0]))

    return FieldSetNode(fields.split(','), variable_name, form)

get_fieldset = register.tag(get_fieldset)


class FieldSetNode(template.Node):
    def __init__(self, fields, variable_name, form_variable):
        self.fields = fields
        self.variable_name = variable_name
        self.form_variable = form_variable

    def render(self, context):
        form = template.Variable(self.form_variable).resolve(context)
        new_form = copy.copy(form)
        new_dict = OrderedDict()
        for field in self.fields:
            if field in form.fields:
                new_dict[field] = form.fields[field]
        new_form.fields = new_dict
        context[self.variable_name] = new_form
        return u''
