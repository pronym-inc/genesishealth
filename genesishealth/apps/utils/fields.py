from django.db import models


class SeparatedValuesField(models.TextField):
    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        sub_choices = kwargs.pop('sub_choices', None)
        if sub_choices:
            self.sub_choices = map(lambda x: x[0], sub_choices)
        else:
            self.sub_choices = None
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return value
        return value.split(self.token)

    def get_prep_value(self, value):
        if not value:
            return
        if self.sub_choices:
            for v in value:
                assert v in self.sub_choices
        return self.token.join([str(s) for s in value])
