import math

from django.db import models


class ProductTypeManager(models.Manager):
    def get_control_solution_type(self):
        return self.get(category=ProductType.CATEGORY_CONTROL_SOLUTION)

    def get_gdrive_type(self):
        return self.get(category=ProductType.CATEGORY_GDRIVE)

    def get_lancet_type(self):
        return self.get(category=ProductType.CATEGORY_LANCET)

    def get_lancing_device_type(self):
        return self.get(category=ProductType.CATEGORY_LANCING_DEVICE)

    def get_strip_type(self):
        return self.get(category=ProductType.CATEGORY_STRIPS)


class ProductType(models.Model):
    CATEGORY_STRIPS = 'strips'
    CATEGORY_GDRIVE = 'gdrive'
    CATEGORY_LANCET = 'lancet'
    CATEGORY_LANCING_DEVICE = 'lancing device'
    CATEGORY_CONTROL_SOLUTION = 'control solution'
    CATEGORY_PAMPHLET = 'pamphlet'

    CATEGORY_CHOICES = (
        (CATEGORY_STRIPS, "Reading Strips"),
        (CATEGORY_GDRIVE, "Glucose Device"),
        (CATEGORY_LANCET, "Lancets"),
        (CATEGORY_LANCING_DEVICE, "Lancing Device"),
        (CATEGORY_CONTROL_SOLUTION, "Control Solution"),
        (CATEGORY_PAMPHLET, "Pamphlet")
    )

    name = models.CharField(max_length=255, unique=True)
    part_number = models.CharField(max_length=255, unique=True)
    unit = models.CharField(max_length=255)
    category = models.CharField(
        max_length=255,
        choices=CATEGORY_CHOICES,
        null=True,
        unique=True)
    description = models.TextField()
    manufacturer = models.CharField(max_length=255)
    is_device = models.BooleanField(
        default=False, verbose_name='Glucose Device')
    is_refill = models.BooleanField(
        default=False, verbose_name='Strip refill item')
    is_bulk = models.BooleanField(
        default=False,
        help_text='If yes, this field will show up only in bulk orders.')
    box_quantity = models.PositiveIntegerField(default=1)

    objects = ProductTypeManager()

    class Meta:
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name

    def convert_to_boxes(self, unit_count):
        return int(math.ceil(float(unit_count) / self.box_quantity))

    def convert_to_units(self, box_count):
        return box_count * self.box_quantity
