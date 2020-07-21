import re
from datetime import datetime, timedelta
import pytz

from django import forms
from django.db.models import ForeignKey
from django.conf import settings
from django.template.loader import render_to_string

from localflavor.us.forms import USZipCodeField

from genesishealth.apps.utils.func import (
    get_attribute_extended, set_attribute_extended, utcnow, read_csv_file)
from genesishealth.apps.accounts.models import PhoneNumber


class SecurityQuestionWidget(forms.Widget):
    """
    This widget just returns the value of the field as text, so
    it doesn't render an actual form field.
    """
    def render(self, name, value, attrs=None, renderer=None):
        return value

    def value_from_datadict(self, data, files, name):
        return data.get(name, '')


class MultiItemWidget(forms.Widget):
    def render(self, name, value, *args, **attrs):
        try:
            count = len(value)
            value = enumerate(value)
        except TypeError:
            value = None
            count = 0

        attrs.update({'name': name, 'value': value, 'count': count})
        return render_to_string(self.template_name, attrs)

    def value_from_datadict(self, data, files, name):
        items = {}
        for k, v in data.items():
            if k.startswith('%s_' % name):
                res = re.findall(r'^%s_(\d+)_(.+?)$' % name, k)
                if len(res) <= 0:
                    continue
                count, variable = res[0]
                if count not in items.keys():
                    items[count] = {'count': int(count)}
                items[count][variable] = v
        list_form = sorted(items.values(), key=lambda x: x['count'])
        return list_form


class PhoneWidget(MultiItemWidget):
    template_name = 'accounts/form_widgets/phone_widget.html'

    def value_from_datadict(self, data, files, name):
        data = super(PhoneWidget, self).value_from_datadict(data, files, name)
        phone_numbers = []
        if data:
            for item in data:
                if item['phone'].strip() == '' and 'pk' not in item:
                    continue
                kwargs = {'phone': item['phone']}
                if 'pk' in item:
                    kwargs['pk'] = item['pk']
                if 'is_cell' in item:
                    kwargs['is_cell'] = True
                if 'is_contact' in item:
                    kwargs['is_contact'] = True
                phone_numbers.append(PhoneNumber(**kwargs))
        return phone_numbers


class PhoneField(forms.Field):
    widget = PhoneWidget()


PHONE_RE = re.compile(r'^\([0-9]{3}\)\s[0-9]{3}-[0-9]{4}$')


class PhoneNumberFormMixin(object):
    def __init__(self, *args, **kwargs):
        super(PhoneNumberFormMixin, self).__init__(*args, **kwargs)
        if not hasattr(self, 'is_new') or not self.is_new:
            self.fields['phone'].initial = self.get_phone_initialdata()

    def clean_phone(self):
        phones = self.cleaned_data.get('phone')
        for pn in phones:
            if pn.phone == '' and pn.id:
                continue
            if not PHONE_RE.match(pn.phone):
                raise forms.ValidationError(
                    "Enter phone number in the format (XXX) XXX-XXXX.")
        return phones

    def get_phone_initialdata(self):
        raise NotImplementedError()

    def save_phone(self, contact):
        data = self.cleaned_data
        for pn in data.get('phone'):
            if pn.id:
                # NOTE: Silently fail to edit phone numbers of another contact
                try:
                    contact.phone_numbers.get(id=pn.id)
                except PhoneNumber.DoesNotExist:
                    continue
            if pn.phone:
                pn.contact = contact
                pn.save()
            elif pn.id:
                pn.delete()


class SinglePhoneField:
    pass


class ZipField(USZipCodeField):
    widget = forms.TextInput(attrs={'class': 'zip'})


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_reversed_name()


class BirthdayWidget(forms.Widget):
    """Widget for a birthday."""
    def render(self, name, value, attrs=None, renderer=None):
        year_range = range(
            (utcnow() - timedelta(days=100 * 365)).year, utcnow().year)
        years = [(i, i) for i in year_range]
        years = sorted(years, key=lambda x: x[0], reverse=True)
        months = []
        for i in range(1, 13):
            months.append(
                (i, datetime(day=1, month=i, year=2000).strftime('%B')))
        days = [(i, i) for i in range(1, 32)]
        return render_to_string(
            'utils/birthday_widget.html',
            {'widget': self, 'name': name, 'value': value,
             'attrs': attrs, 'years': years, 'months': months, 'days': days,
             'required': self.attrs.get('required', False)})

    def value_from_datadict(self, data, files, name):
        try:
            return datetime(
                day=int(data.get('%s_day' % name)),
                month=int(data.get('%s_month' % name)),
                year=int(data.get('%s_year' % name)), tzinfo=pytz.utc)
        except (TypeError, ValueError):
            return None


class GenesisForm(forms.Form):
    required_css_class = "required"
    error_css_class = "invalid"

    def __init__(self, *args, **kwargs):
        super(GenesisForm, self).__init__(*args, **kwargs)
        self.genesis_form_init()


def traverse_by_field(model, field_description):
    split = field_description.split('.')
    next = split[0]
    remainder = ".".join(split[1:])
    for field in model._meta.fields:
        if field.name == next and isinstance(field, ForeignKey):
            next_model = field.remote_field.model
            if remainder:
                return traverse_by_field(next_model, remainder)
            else:
                return next_model

    if hasattr(model, next):
        if remainder:
            return traverse_by_field(getattr(model, next), remainder)
        else:
            return getattr(model, next)

    raise ValueError


class GenesisModelForm(forms.ModelForm):
    SELF_CONSTANT = '_SELF_'
    required_css_class = "required"
    error_css_class = "invalid"

    """These should be names of other related objects that should be created before
    the object."""
    models_i_depend_on = []

    def __init__(self, *args, **kwargs):
        super(GenesisModelForm, self).__init__(*args, **kwargs)
        self.is_new = self.instance.pk is None
        self.genesis_form_init()
        if not self.is_new:
            fields_by_object = self.get_fields_by_object()
            for model_name, field_names in fields_by_object.items():
                if model_name == GenesisModelForm.SELF_CONSTANT:
                    continue
                related_instance = get_attribute_extended(
                    self.instance, model_name)
                for field_name in field_names:
                    self.fields[field_name].initial = getattr(
                        related_instance, field_name)

    def get_all_models(self):
        models = {GenesisModelForm.SELF_CONSTANT: self.instance.__class__}
        for related_name in self.models_i_depend_on:
            models[related_name] = traverse_by_field(
                self.instance, related_name)
        return models

    def get_fields_by_object(self):
        """Returns a dict with key = object_name and value = tuple of
        fields that belong to it."""
        models = self.get_all_models()
        field_info = {}
        for model_name in self.get_all_models():
            field_info[model_name] = []
        for field_name, field in self.fields.items():
            for model_name, available_model in models.items():
                for model_field in available_model._meta.fields:
                    if model_field.name == field_name:
                        field_info[model_name].append(field_name)
                        break
                else:
                    continue
                break

        return field_info

    def get_model_by_name(self, name):
        return self.get_all_models()[name]

    def save(self, commit=True, *args, **kwargs):
        fields_by_object = self.get_fields_by_object()
        pre_objects = {}
        # Manage objects that we depend on
        for model_name in self.models_i_depend_on:
            if self.is_new:
                model = self.get_model_by_name(model_name)
                new_instance = model()
            else:
                new_instance = get_attribute_extended(
                    self.instance, model_name)

            for field in fields_by_object[model_name]:
                setattr(new_instance, field, self.cleaned_data.get(field))
            new_instance.save()
            pre_objects[model_name] = new_instance

        # Save the instance
        new_object = super(GenesisModelForm, self).save(commit=False)

        for model_name in self.models_i_depend_on:
            set_attribute_extended(
                self.instance, model_name, pre_objects[model_name])

        if commit:
            new_object.save()

        return new_object


def add_widget_class(self, field_name, new_class):
    field = self.fields.get(field_name)
    assert field is not None, "Invalid field name passed to add_widget_class"
    widget = field.widget
    classes = widget.attrs.get('class', '').split()
    if new_class not in classes:
        classes.append(new_class)
    widget.attrs['class'] = ' '.join(classes)


def genesis_form_init(self):
    for field_name, field in self.fields.items():
        if (field.required and not field.widget.attrs.get('required') and
                not isinstance(field.widget, forms.CheckboxSelectMultiple)):
            field.widget.attrs['required'] = 'required'
        if isinstance(field, forms.DateTimeField):
            if not field.input_formats:
                field.input_formats = []
            field.input_formats = tuple(field.input_formats) + (
                settings.DATETIME_INPUT_FORMATS)
            self.add_widget_class(field_name, 'dateTimeField')
        elif isinstance(field, forms.DateField):
            if not field.input_formats:
                field.input_formats = []
            field.input_formats = tuple(field.input_formats) + (
                settings.DATE_INPUT_FORMATS)
            self.add_widget_class(field_name, 'dateField')
        elif isinstance(field, forms.TimeField):
            if not field.input_formats:
                field.input_formats = []
            field.input_formats = tuple(field.input_formats) + (
                settings.TIME_INPUT_FORMATS)
            self.add_widget_class(field_name, 'timeField')


GenesisForm.genesis_form_init = GenesisModelForm.genesis_form_init = \
    genesis_form_init
GenesisForm.add_widget_class = GenesisModelForm.add_widget_class = \
    add_widget_class


class GenesisBatchForm(GenesisForm):
    def __init__(self, *args, **kwargs):
        self.batch_queryset = kwargs.pop('batch_queryset')
        try:
            self.batch = self.batch_queryset.filter(pk__in=list(kwargs.pop('batch')))
        except KeyError:
            raise Exception('GenesisBatchForm did not receive a batch in kwargs.')
        super(GenesisBatchForm, self).__init__(*args, **kwargs)

    def has_no_fields(self):
        return len(self.fields) == 0


class GenesisImportForm(GenesisForm):
    line_form_class = None
    import_file = forms.FileField()
    csv_headers = []
    skip_lines = 1

    def __init__(self, *args, **kwargs):
        self.error_map = {}
        super(GenesisImportForm, self).__init__(*args, **kwargs)

    def clean_import_file(self):
        row_forms = self.get_row_forms()
        for row_num, row_form in enumerate(
                row_forms, start=1 + self.skip_lines):
            if not row_form.is_valid():
                self.error_map[row_num] = row_form.errors
        if self.error_map:
            for key in sorted(self.error_map.keys()):
                row_errors = self.error_map[key]
                for field, err in row_errors.items():
                    terr = ("Line {0} - {1}: {2}".format(
                        key, field, ", ".join(err)))
                    self.add_error(None, terr)

    def get_row_forms(self):
        if not hasattr(self, '_forms'):
            forms = []
            rows = read_csv_file(
                self.cleaned_data['import_file'],
                self.csv_headers,
                skip_lines=self.skip_lines)
            for row in rows:
                forms.append(self.line_form_class(row))
            self._forms = forms
        return self._forms

    def save(self):
        row_forms = self.get_row_forms()
        for row_form in row_forms:
            row_form.save()
