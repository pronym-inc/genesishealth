import json

from django.forms.fields import Field
from django.forms import ValidationError as FormValidationError
from django.utils.translation import ugettext_lazy as _


class JSONField(Field):
    def clean(self, value):

        if not value and not self.required:
            return None

        value = super(JSONField, self).clean(value)

        if isinstance(value, str):
            try:
                json.loads(value)
            except ValueError:
                raise FormValidationError(_("Enter valid JSON"))
        return value
