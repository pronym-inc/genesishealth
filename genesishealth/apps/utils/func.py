import io
import pytz
import re

from csv import DictReader
from datetime import datetime
from urllib.request import urlopen

from django.conf import settings
from django.db import models
from django.utils import formats, timezone


def system_message(request, message):
    if not hasattr(request, 'session'):
        raise Exception('Session variable not present on request.')
    if not request.session.get('system_messages'):
        request.session['system_messages'] = []
    request.session['system_messages'].append(message)
    request.session.modified = True


def convert_render_datetime(date):
    """ Convert datetime to locale. Return formatted date. """
    tz = timezone.get_current_timezone()
    return formats.date_format(date.astimezone(tz), 'DATETIME_FORMAT')


def get_attribute(obj, attribute, failsafe=None, not_flag=False, func_args=None):
    """Traverses object attributes similar to how templates work."""
    if func_args is None:
        func_args = []
    if obj is None:
        return None

    if attribute.startswith('!'):
        not_flag = True
        cleaned_attribute = attribute[1:]
    else:
        cleaned_attribute = attribute

    attr_split = cleaned_attribute.split('.')
    attr = getattr(obj, attr_split[0], failsafe)

    if callable(attr) and not isinstance(attr, models.Manager):
        if len(attr_split) == 1:
            """Use func_args on final attribute if it's a function."""
            attr = attr(*func_args)
        else:
            attr = attr()

    if len(attr_split) == 1:
        if not_flag:
            return not attr
        else:
            if isinstance(attr, list) or isinstance(attr, tuple):
                attr = ', '.join(attr)
            return attr
    else:
        remainder = '.'.join(attr_split[1:])
        return get_attribute(attr, remainder, failsafe=failsafe,
                             not_flag=not_flag, func_args=func_args)


def get_attribute_extended(in_obj, extended_name):
    """Example: get_attribute_extended(my_user, 'profile.contact')
    would return my_user.profile.contact."""
    split_name = extended_name.split('.')
    try:
        new_obj = getattr(in_obj, split_name[0])
    except:
        return
    if callable(new_obj):
        new_obj = new_obj()
    if len(split_name) > 1:
        # If that wasn't last item, traverse down one and recurse.
        new_name = '.'.join(split_name[1:])
        return get_attribute_extended(new_obj, new_name)
    return new_obj


def set_attribute_extended(in_obj, extended_name, val):
    split_name = extended_name.split('.')
    next = split_name[0]
    remainder = split_name[1:]
    if remainder:
        next_obj = getattr(in_obj, next)
        set_attribute_extended(next_obj, '.'.join(remainder), val)
    else:
        setattr(in_obj, next, val)


def filter_dict_to_model_fields(in_dict, model):
    """Given a dictionary, it will return a copy of the dictionary that
    only contains fields with names that match a field name on the model."""
    new_dict = {}
    field_names = [f.name for f in model._meta.get_fields() if f.concrete]
    for k, v in in_dict.iteritems():
        if k in field_names:
            new_dict[k] = v
    return new_dict


def read_csv_file(csv_file, field_names, skip_lines=None):
    if skip_lines is None:
        skip_lines = settings.CSV_NUMBER_OF_HEADER_ROWS
    data = []
    # Fix CSV file to conform to different system's new line handling.
    fixed_csv = io.StringIO(str(csv_file.read()), newline=None)
    # Skip some number of lines.
    for i in range(skip_lines):
        fixed_csv.readline()
    for line in DictReader(fixed_csv, field_names, 'extra', ''):
        for k, v in line.iteritems():
            try:
                line[k] = v.strip()
            except AttributeError:
                pass
        data.append(line)
    return data


def utcnow():
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def convert_date_to_utc_datetime(date, timezone):
    """Takes a date object and translates it from the given timezone to UTC."""
    dt = datetime.combine(date, utcnow().time()).replace(tzinfo=timezone)
    return dt.astimezone(pytz.utc)


def get_public_ip():
    """Gets public IP."""
    try:
        data = str(urlopen(settings.PUBLIC_IP_CHECK_URL).read())
    except IOError:
        return 'Unknown'
    return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)


def compare_phone_numbers(number1, number2):
    """Strips away formatting and compares two phone numbers."""
    def clean_number(number):
        return re.sub('[^\d]', '', number)

    return clean_number(number1) == clean_number(number2)


def expand_birthday_year(year):
    """
    Helper function to expand a 2 diget date of birth to the full year.
    If the year is 2013. 12 becomes 2012. 13 is 2013. 14 becomes 1914.
    """
    year = int(year)
    this_year = utcnow().year
    century = int('{0}00'.format(str(this_year)[:-2]))
    full_year = century + year
    if year > int(str(this_year)[-2:]):
        full_year = full_year - 100
    return full_year


def get_home_view_name(user):
    if user.is_staff:
        return 'accounts:manage-users'
    return 'dashboard:home'
