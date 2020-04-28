from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import (
    GenesisTableView, GenesisAboveTableButton, ActionTableColumn,
    AttributeTableColumn, GenesisTableLink, GenesisTableLinkAttrArg,
    ActionItem, GenesisFormView)
from genesishealth.apps.utils.request import admin_user

from .forms import ProductTypeForm
from .models import ProductType


class ProductTypeTableView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('Name', 'name'),
            AttributeTableColumn('Part Number', 'part_number'),
            AttributeTableColumn('Unit', 'unit'),
            AttributeTableColumn('Description', 'description'),
            AttributeTableColumn('Manufacturer', 'manufacturer'),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'Detail',
                        GenesisTableLink(
                            'products:edit',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_above_table_items(self):
        return [
            GenesisAboveTableButton(
                'Import Products',
                reverse('products:import')
            ),
            GenesisAboveTableButton(
                'Add Product',
                reverse('products:add')
            )
        ]

    def get_page_title(self):
        return 'Products'

    def get_queryset(self):
        return ProductType.objects.all()
index = user_passes_test(admin_user)(ProductTypeTableView.as_view())


class AddProductTypeFormView(GenesisFormView):
    form_class = ProductTypeForm
    go_back_until = ['products:index']
    success_message = 'The product type has been added.'
    page_title = 'Add Product Type'

    def get_breadcrumbs(self):
        return [Breadcrumb('Products', reverse('products:index'))]
add_product_type = user_passes_test(admin_user)(
    AddProductTypeFormView.as_view())


class EditProductTypeFormView(GenesisFormView):
    form_class = ProductTypeForm
    go_back_until = ['products:index']
    success_message = 'The product type has been updated.'

    def get_breadcrumbs(self):
        return [Breadcrumb('Products', reverse('products:index'))]

    def get_form_kwargs(self):
        kwargs = super(EditProductTypeFormView, self).get_form_kwargs()
        kwargs['instance'] = self.get_product_type()
        return kwargs

    def get_page_title(self):
        return 'Edit Product Type {0}'.format(self.get_product_type().name)

    def get_product_type(self):
        if not hasattr(self, '_product_type'):
            self._product_type = ProductType.objects.get(
                pk=self.kwargs['product_type_id'])
        return self._product_type
edit_product_type = user_passes_test(admin_user)(
    EditProductTypeFormView.as_view())


def import_product_types(request):
    pass
