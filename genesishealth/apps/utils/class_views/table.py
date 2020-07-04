import json

from datetime import datetime, date
from urllib.parse import urlencode

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.urls import reverse
from django.db.models import FieldDoesNotExist, Q
from django.db.models.fields.related import ForeignObjectRel, ManyToOneRel
from django.http import Http404, HttpResponse
from django.template import Context, Template
from django.template.loader import get_template, render_to_string

from genesishealth.apps.utils.exceptions import ConditionNotMetException
from genesishealth.apps.utils.func import (
    convert_render_datetime, get_attribute)
from genesishealth.apps.utils.class_views.auth_base import AuthTemplateView


class GenesisBaseAboveTableItem(object):
    _is_button = False
    _is_dropdown = False
    _is_raw = False
    _is_radio = False

    def __init__(self, required_user_types=None):
        if required_user_types is None:
            required_user_types = []
        self.required_user_types = required_user_types

    def is_button(self):
        return self._is_button

    def is_dropdown(self):
        return self._is_dropdown

    def is_raw(self):
        return self._is_raw

    def is_radio(self):
        return self._is_radio

    def should_render(self, user):
        if len(self.required_user_types) == 0:
            return True

        for rut in self.required_user_types:
            try:
                if getattr(user, 'is_{}'.format(rut))():
                    return True
            except AttributeError:
                raise Exception('Invalid user type: %s' % rut)
        return False


class GenesisAboveTableButton(GenesisBaseAboveTableItem):
    _is_button = True

    def __init__(self, name, link=None, button_class=None, button_id=None,
                 prefix=None, **kwargs):
        super(GenesisAboveTableButton, self).__init__(**kwargs)
        self.name = name
        if link is not None:
            if prefix is None:
                prefix = settings.DASHBOARD_PREFIX
            self.link = "{}{}".format(prefix, link)
        else:
            self.link = "#"
        self.button_class = button_class
        self.button_id = button_id


class GenesisDropdownOption(object):
    def __init__(self, display, value, direct_link=False,
                 no_redirect=False):
        self.display = display
        self.value = value
        self.direct_link = direct_link
        self.no_redirect = no_redirect


class GenesisAboveTableDropdown(GenesisBaseAboveTableItem):
    _is_dropdown = True

    def __init__(self, options, **kwargs):
        super(GenesisAboveTableDropdown, self).__init__(**kwargs)
        self.options = options


class GenesisAboveTableRaw(GenesisBaseAboveTableItem):
    _is_raw = True

    def __init__(self, content, **kwargs):
        super(GenesisAboveTableRaw, self).__init__(**kwargs)
        self.content = content


class GenesisAboveTableTemplateItem(GenesisAboveTableRaw):
    def __init__(self, template_name, context=None, **kwargs):
        if context is None:
            context = {}
        template = get_template(template_name)
        content = template.render(context)
        super(GenesisAboveTableTemplateItem, self).__init__(content)


class GenesisAboveTableRadio(GenesisBaseAboveTableItem):
    _is_radio = True

    def __init__(self, options, **kwargs):
        super(GenesisAboveTableRadio, self).__init__(**kwargs)
        self.options = options


class GenesisTableLinkAttrArg(object):
    def __init__(self, attribute_name):
        self.attribute_name = attribute_name

    def resolve(self, obj):
        return get_attribute(obj, self.attribute_name)


class GenesisTableLink(object):
    def __init__(self, url_name, for_user_type=None,
                 url_args=None, query_string=None,
                 prefix=settings.DASHBOARD_PREFIX):
        if url_args is None:
            url_args = []
        self.url_name = url_name
        self.for_user_type = for_user_type
        self.url_args = url_args
        self.query_string = query_string
        self.prefix = prefix

    def available_to_user(self, user):
        if self.for_user_type:
            user_type = user.get_user_type()
            return user_type == self.for_user_type
        return True

    def parse(self, obj, user, prefix=None):
        if prefix is None:
            prefix = self.prefix
        assert self.available_to_user(user)
        args = []
        for link_arg in self.url_args:
            if isinstance(link_arg, GenesisTableLinkAttrArg):
                args.append(link_arg.resolve(obj))
            else:
                args.append(link_arg)
        link = '{}{}'.format(
            prefix,
            reverse(self.url_name, args=args))

        if self.query_string is not None:
            link += '?{}'.format(
                urlencode(self.query_string)
            )
        return link


class GenesisTableCell(object):
    def __init__(self, content, cell_class=None):
        self.content = content
        self.cell_class = cell_class


class BaseTableColumn(object):
    def __init__(self,
                 name, cell_class=None, searchable=True,
                 sortable=True, hide_for_user_types=None,
                 default_sort=None, default_sort_direction='asc'):
        if hide_for_user_types is None:
            hide_for_user_types = []
        self.name = name
        self.cell_class = cell_class
        self.searchable = searchable
        self.sortable = sortable
        self.hide_for_user_types = hide_for_user_types
        self.default_sort = default_sort
        self.default_sort_direction = default_sort_direction

    def available_to_user(self, user):
        user_type = user.get_user_type()
        return user_type not in self.hide_for_user_types

    def render_cell(self, obj, user):
        content = self.get_content(obj, user)
        return GenesisTableCell(
            content, cell_class=self.cell_class)

    def set_sort(self, idx):
        if self.default_sort:
            self.sort = '[[ {}, "{}" ]]'.format(
                idx, self.default_sort_direction)
        else:
            self.sort = None


class AttributeTableColumn(BaseTableColumn):
    def __init__(
            self, name, attribute_name, failsafe='',
            func_args=None, truncate=False, string_format=None,
            proxy_field=None, **kwargs):
        super(AttributeTableColumn, self).__init__(name, **kwargs)
        self.attribute_name = attribute_name
        self.failsafe = None
        if func_args is None:
            self.func_args = []
        else:
            self.func_args = func_args
        self.truncate = truncate
        self.string_format = string_format
        self.proxy_field = proxy_field

    def get_column_name(self):
        if self.proxy_field:
            return self.proxy_field
        return self.attribute_name

    def get_content(self, obj, user):
        content = get_attribute(
            obj,
            self.attribute_name,
            failsafe=self.failsafe,
            func_args=self.func_args)
        if isinstance(content, bool):
            content = 'Yes' if content else 'No'
        elif isinstance(content, date) and not isinstance(content, datetime):
            content = content.strftime('%x')
        if self.truncate:
            content = self._smart_truncate(
                content,
                self.truncate
            )
        if self.string_format:
            if content:
                content = self.string_format % content
        return content

    def _smart_truncate(self, content, length=100, suffix='...'):
        if len(content) <= length:
            return content
        return content[:length].rsplit(' ', 1)[0] + suffix


class ActionButton(object):
    def __init__(self, name, link, link_name, data_attributes=None):
        self.name = name
        self.link = link
        self.link_name = link_name
        if data_attributes is None:
            self.data_attributes = []
        else:
            self.data_attributes = data_attributes


class ActionItem(object):
    def __init__(
            self, name, link, condition=None, required_user_types=None,
            link_href=None, link_data_attrs=None):
        self.name = name
        self.link = link
        self.condition = condition
        self.required_user_types = required_user_types
        self.link_href = link_href
        self.link_data_attrs = link_data_attrs

    def render_button(self, obj, user):
        data_attrs = []
        if self.link_href:
            link = self.link_href
        else:
            link = self.link.parse(obj, user)
        if self.link_data_attrs:
            for (attr_name, obj_key) in self.link_data_attrs:
                data_attrs.append({'key': attr_name,
                                   'value': get_attribute(obj, obj_key)})
        if self.link is not None:
            url_name = self.link.url_name
        else:
            url_name = None
        return ActionButton(
            self.name,
            link,
            url_name,
            data_attributes=data_attrs)

    def should_render(self, obj, user):
        if self.required_user_types:
            found = False
            for rut in self.required_user_types:
                try:
                    test = getattr(user, 'is_%s' % rut)
                    if test():
                        found = True
                        break
                except AttributeError:
                    raise Exception('Invalid user type: %s' % rut)
            if not found:
                return False
        allowed = False
        if self.condition:
            try:
                for iitem in self.condition:
                    if iitem[0] == '!':
                        not_flag = True
                        if_item = iitem[1:]
                    else:
                        not_flag = False
                        if_item = iitem

                    attr_content = get_attribute(obj, if_item)
                    if not_flag:
                        attr_content = not attr_content
                    if not attr_content:
                        raise ConditionNotMetException
                    else:
                        allowed = True
                    if not allowed:
                        continue
            except ConditionNotMetException:
                return False
        return True


class ActionTableColumn(BaseTableColumn):
    def __init__(self, name, actions, **kwargs):
        kwargs.setdefault('sortable', False)
        kwargs.setdefault('searchable', False)
        super(ActionTableColumn, self).__init__(name, **kwargs)
        self.actions = actions

    def get_content(self, obj, user):
        buttons = []
        for action in self.actions:
            if action.should_render(obj, user):
                buttons.append(action.render_button(obj, user))
        out = render_to_string(
            'utils/generic_table_templates/action_buttons.html',
            {'buttons': buttons}
        )
        return out

    def parse(self, action, user, obj=None, prefix=settings.DASHBOARD_PREFIX):
        assert self.available_to_user(user)
        args = []
        for link_arg in self.url_args:
            args.append(link_arg.get_value(obj))
        link = '{}{}'.format(
            prefix,
            reverse(self.url_name, args=args))

        if self.query_string is not None:
            link += '?{}'.format(
                urlencode(self.query_string)
            )
        return link


class GenesisTableBase(object):
    additional_css_templates = []
    additional_js_templates = []
    extra_search_fields = []

    def __init__(self, *args, **kwargs):
        self._user = None

    def get_additional_css(self):
        css_files = self.get_additional_css_templates()
        css_str = ''
        for csf in css_files:
            if len(csf) == 2:
                c = csf[1]
            else:
                c = {}
            css_str += render_to_string(csf[0], c)
        return css_str

    def get_additional_css_templates(self):
        return self.additional_css_templates

    def get_additional_js(self):
        js_files = self.get_additional_js_templates()
        request = self.get_request()
        if self.is_batch():
            js_files.append([
                'utils/generic_table_templates/batch_select_js.html',
                {'csrf_token': request.COOKIES.get('csrftoken')}
            ])
        js_str = ''
        for jsf in js_files:
            if len(jsf) == 2:
                c = jsf[1]
            else:
                c = {}
            js_str += render_to_string(jsf, c)
        return js_str

    def get_additional_js_templates(self):
        return self.additional_js_templates

    def get_request(self):
        return

    def get_user(self):
        if self._user:
            return self._user
        request = self.get_request()
        return request.user

    def render_above_table_items(self):
        items = []
        user = self.get_user()
        for item in self._get_above_table_items():
            if item.should_render(user):
                items.append(item)

        return render_to_string(
            'utils/generic_table_templates/above_table.html',
            {'items': items}
        )


class GenesisSingleTableBase(GenesisTableBase):
    force_batch = False
    ajax = True
    above_table_items = []
    headerless = False
    name_postfix = ''
    records_per_page = 10
    fake_count = False
    skip_ajax_sort = False
    ajax_limit = 1000
    focus_on_load = True

    def __init__(self, parent=None, request=None, view_kwargs=None):
        self._parent = parent
        self._request = request
        self._view_kwargs = view_kwargs
        self._ati = None
        self._is_batch = None
        self._columns = []
        self._columns_assembled = False
        super(GenesisSingleTableBase, self).__init__()

    def add_column(self, column):
        user = self.get_user()
        if column.available_to_user(user):
            self._columns.append(column)

    def add_columns(self, *columns):
        for column in columns:
            self.add_column(column)

    def create_columns(self):
        return []

    def generate_batch_select_box(self, obj):
        template = Template(
            """<input type="checkbox" name="batch_{{ obj.id }}" class="batchSelectBox" />""")  # noqa
        content = template.render(Context({'obj': obj}))
        return GenesisTableCell(content)

    def generate_rows(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        rows = []
        user = self.get_user()
        for obj in queryset:
            cells = []
            if self.is_batch():
                cells.append(self.generate_batch_select_box(obj))
            for column in self.get_columns():
                if column.available_to_user(user):
                    cells.append(column.render_cell(obj, user))
            rows.append(cells)
        return rows

    def _get_above_table_items(self):
        if self._ati is None:
            self._ati = self.get_above_table_items()
        return self._ati

    def get_above_table_items(self):
        return []

    def get_ajax_limit(self):
        return settings.TABLE_DEFAULT_AJAX_LIMIT

    def get_ajax_response(self, request):
        # Item count
        queryset = self.get_queryset()
        if self.fake_count:
            total_count = 10000
        else:
            total_count = queryset.count()

        json_data = {
            'aaData': [],
            'iTotalRecords': total_count,
            'iTotalDisplayRecords': total_count
        }
        search_terms = request.GET.get('sSearch', '').lower().strip().split()
        filtered_queryset = queryset

        # Figure out the queryable columns for sorting and searching.
        def check_for_field(model, field_name):
            try:
                return model._meta.get_field(field_name)
            except FieldDoesNotExist:
                return False
        queryable_columns = []
        do_distinct = False
        for column_index, column in enumerate(self.get_columns()):
            if (not isinstance(column, AttributeTableColumn) or
                    not column.searchable):
                continue
            failed = False
            column_name = column.get_column_name()
            u_split = column_name.split('.')
            model = queryset.model
            for index, attr in enumerate(u_split):
                """The logic is a little complex here.  What we're trying to do
                is iterate through the "dot" attributes until we verify that
                the final attribute in the chain is NOT another related field,
                which would mean we could not query it with our search.  In
                other words, we are compiling all of the attributes in the
                table which are queryable.

                The logic is:

                1) Check if the attribute even exists on the model as a field;
                  if not, abort.
                2) If it exists and it is a related field (e.g. foreignkey),
                    then ignore it if it's the last element to be searched.
                    If it is not the last element in the dot chain, then go
                    back through the loop using the model associated with the
                    related field until we do get to the end."""
                f_ = check_for_field(model, attr)
                if not f_:
                    failed = True
                    break
                if isinstance(f_, ForeignObjectRel):
                    if isinstance(f_, ManyToOneRel):
                        do_distinct = True
                    new_model = f_.model
                    if new_model == model:
                        new_model = getattr(
                            f_, 'related_model', new_model)
                elif (getattr(f_, 'remote_field', None) and
                        f_.remote_field.model):
                    new_model = f_.remote_field.model
                else:
                    new_model = None
                if new_model:
                    if index == len(u_split) - 1:
                        failed = True
                        break
                    model = new_model
                elif index != len(u_split) - 1:
                    failed = True
                    break
            # It met all the conditions, so add to the query.
            if not failed:
                queryable_columns.append([
                    column_name.replace('.', '__'),
                    column,
                    column_index
                ])
        for extra_field in self.extra_search_fields:
            queryable_columns.append([
                extra_field, None, None
            ])
        # Handle searching.
        print(queryable_columns)
        if len(search_terms) > 0:
            queries = []
            for term in search_terms:
                query = None
                for column_name, column, column_index in queryable_columns:
                    search_key = "{}__icontains".format(column_name)
                    new_q = Q(**{search_key: term})
                    if query is None:
                        query = new_q
                    else:
                        query |= new_q
                if query is not None:
                    queries.append(query)
            if len(queries) > 0:
                filtered_queryset = filtered_queryset.filter(*queries)
            if not self.fake_count:
                json_data['iTotalDisplayRecords'] = filtered_queryset.count()
        # Handle sorting.
        # First figure out which columns we are sorting.
        sort_indices = []
        for i in range(len(self.get_columns())):
            sort_index = request.GET.get('iSortCol_{}'.format(i))
            if sort_index is not None:
                sort_indices.append([
                    int(sort_index),
                    request.GET.get('sSortDir_{}'.format(i))
                ])
        sort_terms = []
        for column_name, column, column_index in queryable_columns:
            if column_index is None:
                continue
            # See if this column is being sorted.
            if self.is_batch():
                cidx = column_index + 1
            else:
                cidx = column_index
            if column.sortable:
                for sort_index, sort_direction in sort_indices:
                    if sort_index == cidx:
                        sort_term = column_name
                        if sort_direction == 'desc':
                            sort_term = "-{}".format(column_name)
                        else:
                            sort_term = column_name
                        sort_terms.append(sort_term)
        sort_terms.append('id')
        ajax_limit = self.get_ajax_limit()
        if len(sort_terms) > 0 and not self.skip_ajax_sort:
            filtered_queryset = filtered_queryset.order_by(*sort_terms)
        if do_distinct:
            filtered_queryset = filtered_queryset.distinct()
        if ajax_limit:
            filtered_queryset = filtered_queryset[:ajax_limit]
        # Pagination
        page_limit = int(request.GET.get('iDisplayLength', 10))
        page = (int(request.GET.get('iDisplayStart', 0)) / page_limit) + 1
        prefetch_fields = self.get_prefetch_fields()
        paginator = Paginator(
            filtered_queryset.prefetch_related(*prefetch_fields),
            page_limit
        )
        # HACK: Makes paginator not check length of QS which is useful for
        # large queries.
        if self.fake_count:
            paginator._count = ajax_limit
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            items = paginator.page(1)
        except EmptyPage:
            raise Http404
        # Render cell content
        qs = items.object_list
        rows = self.generate_rows(qs)
        for row in rows:
            row_data = []
            for cell in row:
                data = cell.content
                if isinstance(data, datetime):
                    data = convert_render_datetime(data)
                row_data.append(str(data))
            json_data['aaData'].append(row_data)

        return HttpResponse(
            json.dumps(json_data),
            content_type="application/json")

    def get_ajax_url(self):
        return

    def get_columns(self):
        if not self._columns_assembled:
            self._columns = []
            self.add_columns(*self.create_columns())
            self._columns_assembled = True
        return self._columns

    def get_datatable_js(self):
        start_index = 1 if self.is_batch() else 0
        not_searchable_indices = []
        not_sortable_indices = []
        not_sortable_or_searchable_indices = []
        # If it's batch, make sure that we dont make the first
        # checkbox column sortable/searchable
        if self.is_batch():
            not_sortable_or_searchable_indices.append('0')
        for idx, column in enumerate(self.get_columns(), start=start_index):
            searchable = column.searchable
            sortable = column.sortable
            if sortable and not searchable:
                not_searchable_indices.append(str(idx))
            elif searchable and not sortable:
                not_sortable_indices.append(str(idx))
            elif not searchable and not sortable:
                not_sortable_or_searchable_indices.append(str(idx))
            column.set_sort(idx)
        c = {
            'not_searchable': ', '.join(not_searchable_indices),
            'not_sortable': ', '.join(not_sortable_indices),
            'not_searchable_or_sortable': ', '.join(
                not_sortable_or_searchable_indices),
            'ajax': self.ajax,
            'table_name_postfix': self.name_postfix,
            'iDisplayLength': self.records_per_page,
            'focus_on_load': self.focus_on_load
        }
        columns = self.get_columns()
        for column in columns:
            if column.default_sort:
                c['sort'] = '[[ {}, "{}" ]]'.format(
                    columns.index(column),
                    column.default_sort_direction)
                break

        return render_to_string(
            'utils/generic_table_templates/datatable_script_block.html', c)

    def get_kwargs(self):
        if self._view_kwargs is not None:
            return self._view_kwargs
        if self._parent is not None:
            return self._parent.kwargs

    def get_parent(self):
        return self._parent

    def get_prefetch_fields(self):
        return []

    def get_queryset(self):
        raise Exception('Not implemented!')

    def get_request(self):
        if self._request is not None:
            return self._request
        if self._parent is not None:
            return self._parent.request

    def get_table_context(self):
        data = {
            'columns': self.get_columns(),
            'table_name_postfix': self.name_postfix,
            'data_table_js': self.get_datatable_js(),
            'batch_enabled': self.is_batch(),
            'ajax_url': self.get_ajax_url()
        }
        if self.ajax:
            data['rows'] = []
        else:
            data['rows'] = self.generate_rows()
        if not self.headerless:
            data['above_table_content'] = self.render_above_table_items()
        return data

    def is_batch(self):
        if self.force_batch:
            return True
        if self._is_batch is None:
            self._is_batch = False
            for above_table_item in self._get_above_table_items():
                if isinstance(above_table_item, GenesisAboveTableDropdown):
                    self._is_batch = True
                    break
        return self._is_batch

    def render_cell_content(self, obj, column):
        content = get_attribute(
            obj,
            column['attribute'],
            failsafe=column.failsafe,
            func_args=column.func_args)
        if isinstance(content, bool):
            content = 'Yes' if content else 'No'
        return content

    def render_to_string(self):
        context = self.get_table_context()
        template = get_template(
            "utils/generic_table_templates/table_include.html")
        return template.render(context)


class GenesisTableView(AuthTemplateView, GenesisSingleTableBase):
    template_name = 'utils/generic_table_templates/base.html'
    page_title = 'Generic Table'

    def __init__(self, *args, **kwargs):
        super(GenesisTableView, self).__init__(*args, **kwargs)
        GenesisSingleTableBase.__init__(self)

    def get(self, request, *args, **kwargs):
        if request.method == 'GET' and request.GET.get('ajax') == '1':
            return self.get_ajax_response(request)
        return super(GenesisTableView, self).get(request, *args, **kwargs)

    def get_breadcrumbs(self):
        return []

    def get_context_data(self, **kwargs):
        data = super(GenesisTableView, self).get_context_data(**kwargs)
        data.update(self.get_table_context())
        data['title'] = self.get_page_title()
        data['additional_js'] = self.get_additional_js()
        data['additional_css'] = self.get_additional_css()
        data['breadcrumbs'] = self.get_breadcrumbs()
        return data

    def get_page_title(self):
        return self.page_title

    def get_request(self):
        return self.request


class GenesisMultipleTableView(AuthTemplateView, GenesisTableBase):
    template_name = 'utils/generic_table_templates/base_multiple.html'
    table_classes = []
    force_batch = False

    def __init__(self, *args, **kwargs):
        self._tables = {}
        self._table_class_map = None
        self._ati = None
        self._is_batch = None
        super(GenesisMultipleTableView, self).__init__(*args, **kwargs)
        GenesisTableBase.__init__(self)

    def get(self, request, *args, **kwargs):
        if request.method == 'GET' and request.GET.get('ajax') == '1':
            return self.get_ajax_response()
        return super(GenesisMultipleTableView, self).get(
            request, *args, **kwargs)

    def _get_above_table_items(self):
        if self._ati is None:
            self._ati = self.get_above_table_items()
        return self._ati

    def get_above_table_items(self):
        return []

    def get_ajax_response(self):
        assert self.request.method == 'GET'
        prefix = self.request.GET['prefix']
        table = self.get_table(prefix)
        return table.get_ajax_response(self.request)

    def get_breadcrumbs(self):
        return []

    def get_context_data(self, **kwargs):
        data = super(GenesisMultipleTableView, self).get_context_data(**kwargs)
        tables = []
        for table_class in self.get_table_classes():
            table = table_class(parent=self)
            content = table.render_to_string()
            tables.append({
                'html': content,
                'header': table.header,
                'postfix_name': table.name_postfix
            })
        data.update({
            'tables': tables,
            'title': self.get_page_title(),
            'additional_css': self.get_additional_css(),
            'additional_js': self.get_additional_js(),
            'above_table_content': self.render_above_table_items(),
            'breadcrumbs': self.get_breadcrumbs()
        })
        return data

    def get_page_title(self):
        return self.page_title

    def get_request(self):
        return self.request

    def get_table(self, name):
        if name not in self._tables:
            table_class = self.get_table_class(name)
            self._tables[name] = table_class(parent=self)
        return self._tables[name]

    def get_table_class(self, name):
        if self._table_class_map is None:
            self._table_class_map = {
                table_class.name_postfix: table_class for
                table_class in self.get_table_classes()
            }
        return self._table_class_map[name]

    def get_table_classes(self):
        return self.table_classes

    def is_batch(self):
        return False
