from __future__ import absolute_import

from copy import copy
from itertools import chain
import os
import sys
import shlex
import six

from django.conf import settings

from subprocess import check_output


def _options_to_args(**options):
    """Converts ``options`` into a list of command-line arguments."""
    flags = []
    for name in sorted(options):
        value = options[name]
        if value is None:
            continue
        flags.append('--' + name.replace('_', '-'))
        if value is not True:
            if isinstance(value, list):
                flags.extend(value)
            else:
                flags.append(six.text_type(value))
    return flags


def wkhtmltopdf(pages, output=None, **kwargs):
    """
    Converts html to PDF using http://wkhtmltopdf.org/.
    pages: List of file paths or URLs of the html to be converted.
    output: Optional output file path. If None, the output is returned.
    **kwargs: Passed to wkhtmltopdf via _extra_args() (See
              https://github.com/antialize/wkhtmltopdf/blob/master/README_WKHTMLTOPDF
              for acceptable args.)
              Kwargs is passed through as arguments. e.g.:
                  {'footer_html': 'http://example.com/foot.html'}
              becomes
                  '--footer-html http://example.com/foot.html'
              Where there is no value passed, use True. e.g.:
                  {'disable_javascript': True}
              becomes:
                  '--disable-javascript'
              To disable a default option, use None. e.g:
                  {'quiet': None'}
              becomes:
                  ''
    example usage:
        wkhtmltopdf(pages=['/tmp/example.html'],
                    dpi=300,
                    orientation='Landscape',
                    disable_javascript=True)
    """
    if isinstance(pages, six.string_types):
        # Support a single page.
        pages = [pages]

    if output is None:
        # Standard output.
        output = '-'

    # Default options:
    options = getattr(settings, 'WKHTMLTOPDF_CMD_OPTIONS', None)
    if options is None:
        options = {'quiet': True}
    else:
        options = copy(options)
    options.update(kwargs)

    # Force --encoding utf8 unless the user has explicitly overridden this.
    options.setdefault('encoding', 'utf8')

    env = getattr(settings, 'WKHTMLTOPDF_ENV', None)
    if env is not None:
        env = dict(os.environ, **env)

    cmd = 'WKHTMLTOPDF_CMD'
    cmd = getattr(settings, cmd, os.environ.get(cmd, 'wkhtmltopdf'))

    ck_args = list(chain(shlex.split(cmd),
                         _options_to_args(**options),
                         list(pages),
                         [output]))
    ck_kwargs = {'env': env}
    try:
        i = sys.stderr.fileno()
        ck_kwargs['stderr'] = sys.stderr
    except AttributeError:
        # can't call fileno() on mod_wsgi stderr object
        pass

    return check_output(ck_args, **ck_kwargs)
