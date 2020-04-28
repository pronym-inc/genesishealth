from genesishealth.apps.utils.forms import GenesisModelForm

from .models import ProductType


class ProductTypeForm(GenesisModelForm):
    class Meta:
        model = ProductType
        fields = ('name', 'part_number', 'unit', 'description', 'manufacturer',
                  'is_device')
