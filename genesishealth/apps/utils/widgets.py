from itertools import chain

from django import forms
from django.forms.utils import flatatt
from django.forms.widgets import (
    SelectMultiple, format_html, mark_safe)
from django.utils import html
from django.utils.encoding import force_text


class SubmitButtonWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None, choices=()):
        return '<input type="submit" name="{0}" value="{1}">'.format(
            html.escape(name), html.escape(value))


class AdditionalModelMultipleChoiceWidget(SelectMultiple):
    def render(self, name, value, attrs=None, renderer=None,
               choices=(('', '---------'),)):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, {'name': name})
        output = []
        if len(value) == 0:
            output.append(format_html('<select{}>', flatatt(final_attrs)))
            options = self.render_options(choices, [value])
            if options:
                output.append(options)
            output.append('</select>')
        else:
            for val in value:
                output.append(format_html('<select{}>', flatatt(final_attrs)))
                options = self.render_options(choices, [val])
                if options:
                    output.append(options)
                output.append('</select>')
        output.append(
            '<p><a href="#" class="addNewItem">Add Another</a></p>')
        return mark_safe('\n'.join(output))

    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html('<option value="{}"{}>{}</option>',
                           option_value,
                           selected_html,
                           force_text(option_label))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        for option_value, option_label in chain(choices, self.choices):
            if isinstance(option_label, (list, tuple)):
                output.append(
                    format_html(
                        '<optgroup label="{}">', force_text(option_value)))
                for option in option_label:
                    output.append(
                        self.render_option(selected_choices, *option))
                output.append('</optgroup>')
            else:
                output.append(
                    self.render_option(
                        selected_choices, option_value, option_label))
        return '\n'.join(output)

    def value_from_datadict(self, data, files, name):
        try:
            getter = data.getlist
            vals = filter(lambda x: x != '', getter(name))
        except AttributeError:
            getter = data.get
            vals = getter(name)
        return vals
