from django import forms
from django.conf import settings
from django.urls import reverse
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.template.loader import render_to_string

from genesishealth.apps.utils.exceptions import ActionIconException
from genesishealth.apps.utils.forms import GenesisBatchForm, GenesisForm
from genesishealth.apps.utils.request import (
    genesis_redirect, redirect_with_message)
from genesishealth.apps.utils.widgets import SubmitButtonWidget


def generic_form(request, form_class, page_title='', form_kwargs=None,
                 thanks_view_name=None, redirect_kwargs=None,
                 system_message=None, extra_head_template=None,
                 extra_head_context={}, batch=False,
                 batch_variable='batch_ids', only_batch_input=False,
                 batch_queryset=None, redirect_kwargs_from_form_output={},
                 delete_view=None, delete_view_args=[], go_back_until=[],
                 form_template='utils/generic_form.html',
                 extra_form_context={}, back_on_error=False,
                 back_on_error_message=None, extra_js=[], form_message=None,
                 send_download_url=None, breadcrumbs=None,
                 extra_delete_warning=None):
    """
    This function basically takes a form object and generates the form page,
    processes the form,
    runs the save method if successful, and then exits in some way specified
    by the parameters.

    Parameters:

    - request: Django request object [required]
    - form_class: The form class that is to be used [required]
    - page_title: The title of the page that will be rendered
    - thanks_view_name: The view name that the form will redirect to upon
    success.  If unspecified
        it will send the user back one page in history.
    - redirect_kwargs: arguments that will be passed to redirect alongside
    thanks_view_name
    - system_message: system_message that will be added to user's session
    and display on next page view
    - extra_head_template: HTML template including extra head content
    - extra_head_context: for rendering extra_head_template
    - batch: specifies if this is a batch form, which requires some slightly
    different processing
    - batch_variable: the POST key that will be used to determine the IDs of
    the batch_variable
    - only_batch_input: need to mark this as true for batch requests that
    don't have any fields except
        for the batch id's
    - batch queryset: set of permissible objects for batch to get
    - redirect_kwargs_from_form_output: this is a dictionary that is
    formatted as redirect_kwarg_key : obj_attribute
        In other words, if the form is going to return a User object and
        you want to redirect to a page like
        /accounts/patients/<patient_id>/ , pass {'patient_id': 'id'} as
        redirect_kwargs_from_form_output
    - delete_view: View name of the delete function for this page.
    - delete_view_args: Used to get URL of above
    - go_back_until: By default, if no thanks_view_name is provided, user will
    be sent back in their history.
        go_back_until should be a list of two-element tuples.  The first
        element should be a view name and
        the second element (optional) should be positional arguments to pass
        to reverse.  By default, it will
        go back three steps, unless one of the parts of the history matches a
        view in go_back_until.  This is
        useful for sending forms back when you don't know how many clicks away
        they should be - e.g. if you have
        a delete form that is exposed directly on the tabular display and one
        that is exposed on edit screen.
    - form_template: template form should be rendered in
    - extra_form_context: for rendering above
    - back_on_error: Send browser back a page if the form has an error
    - back_on_error_message: System message to append for above
    - send_download_url: True/False indicating whether we should ask the form,
     via,
        get_download_id() method, for a download ID to send along with
        redirect.
    - breadcrumbs - Breadcrumb navigation to be rendered
    - extra_delete_warning - Extra notice to be displayed on confirmation
        page
    """

    if form_kwargs is None:
        form_kwargs = {}
    if redirect_kwargs is None:
        redirect_kwargs = {}
    c = extra_form_context.copy()
    if form_message:
        c['form_message'] = form_message
    c['title'] = page_title
    c['extra_js'] = extra_js
    # Do some pre-processing for batch requests
    if batch:
        assert request.method == 'POST', 'batch mode generic_form requests must be sent over POST' # noqa
        assert isinstance(batch_queryset, QuerySet), 'You must specify a batch_queryset if using a batch form.' # noqa
        post_data = request.POST.copy()
        files_data = request.FILES
        try:
            batch_data = post_data.get(batch_variable)
            post_data.pop(batch_variable)
            form_kwargs['batch'] = list(map(int, batch_data.split(',')))
            form_kwargs['batch_queryset'] = batch_queryset
            c['batch_queryset'] = batch_queryset
        except KeyError:
            raise Exception(
                'generic_form was called in batch mode, but the request did not contain the batch variable (%s)' % batch_variable) # noqa

        c['batch_id_str'] = ','.join(list(map(str, form_kwargs['batch'])))
        if len(post_data) == 1 and post_data.get('csrfmiddlewaretoken'):
            post_data.pop('csrfmiddlewaretoken')
    else:
        post_data = request.POST
        files_data = request.FILES
    if request.method == "POST" and (
            len(post_data) > 0 or (
                batch and only_batch_input) or len(files_data) > 0):
        form = form_class(post_data, files_data, **form_kwargs)
        if form.is_valid():
            obj = form.save()
            if redirect_kwargs_from_form_output:
                redirect_kwargs = {}
                for k, v in redirect_kwargs_from_form_output.items():
                    redirect_kwargs[k] = getattr(obj, v)
            if send_download_url:
                dl_id = form.get_download_id()
                if dl_id:
                    redirect_kwargs['then_download_id'] = \
                        form.get_download_id()
            if system_message:
                return redirect_with_message(
                    request, thanks_view_name, system_message,
                    go_back_until=go_back_until, **redirect_kwargs)
            else:
                return genesis_redirect(
                    request, thanks_view_name, go_back_until=go_back_until,
                    **redirect_kwargs)
        else:
            if back_on_error:
                if back_on_error_message:
                    return redirect_with_message(
                        request, None, back_on_error_message)
                else:
                    return genesis_redirect(request, None)
    else:
        form = form_class(**form_kwargs)
    c['form'] = form

    if extra_head_template:
        c['extra_head'] = render_to_string(
            extra_head_template, extra_head_context)

    if delete_view:
        c['delete_link'] = reverse(delete_view, args=delete_view_args)
    if breadcrumbs is not None:
        c['breadcrumbs'] = breadcrumbs
    if extra_delete_warning is not None:
        c['extra_delete_warning'] = extra_delete_warning

    return render(request, form_template, c)


def generic_dashboard(request, title, content, **kwargs):
    return render(
        request, 'utils/generic.html',
        context={'title': title, 'content': content})


def generic_delete_form(
        request, obj=None, page_title=None, system_message=None,
        go_back_until=[], batch=False, batch_queryset=False, breadcrumbs=None,
        extra_delete_warning=None):
    if obj:
        if isinstance(obj, QuerySet):
            assert obj.count() > 0
            class_name = obj[0]._meta.verbose_name
            objects = obj
        else:
            class_name = obj._meta.verbose_name
            objects = [obj]
    else:
        assert batch
        class_name = batch_queryset.model._meta.verbose_name
        batch_ids = request.POST.get('batch_ids')
        if batch_ids:
            objects = batch_queryset.filter(
                pk__in=request.POST['batch_ids'].split(','))
        else:
            objects = batch_queryset.none()

    if page_title is None:
        page_title = 'Delete %s' % class_name
    if system_message is None:
        system_message = 'The %s has been deleted.' % class_name

    if batch:
        class GenericBatchDeleteForm(GenesisBatchForm):
            SUCCESS = 'Confirm'
            FAILURE = 'Cancel'
            confirm = forms.CharField(
                widget=SubmitButtonWidget, label="", initial="Confirm")

            def clean_confirm(self):
                if self.cleaned_data.get('confirm') == GenericBatchDeleteForm.FAILURE: # noqa
                    raise forms.ValidationError('')
                return self.cleaned_data.get('confirm')

            def save(self):
                for obj in self.batch:
                    obj.delete()

        form_class = GenericBatchDeleteForm
    else:
        class GenericDeleteForm(GenesisForm):
            SUCCESS = 'Confirm'
            FAILURE = 'Cancel'
            confirm = forms.CharField(
                widget=SubmitButtonWidget, label="", initial="Confirm")

            def clean_confirm(self):
                if self.cleaned_data.get('confirm') == GenericDeleteForm.FAILURE: # noqa
                    raise forms.ValidationError('')
                return self.cleaned_data.get('confirm')

            def save(self):
                obj.delete()

        form_class = GenericDeleteForm

    return generic_form(
        request, form_class=form_class, page_title=page_title,
        system_message=system_message,
        form_template='utils/generic_delete_form.html',
        extra_form_context={'objects': objects}, go_back_until=go_back_until,
        back_on_error=True, batch=batch, batch_queryset=batch_queryset,
        breadcrumbs=breadcrumbs, extra_delete_warning=extra_delete_warning)


def get_action_icon(view_name):
    """Used in views to get the icon class to be passed to the table."""
    try:
        return settings.TABLE_ACTION_ICON_CLASSES[view_name]
    except KeyError:
        raise ActionIconException(
            'get_action_icon received an invalid icon name: %s' % view_name)
