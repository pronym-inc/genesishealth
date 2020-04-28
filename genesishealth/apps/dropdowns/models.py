from django.db import models


class GenericNamedModel(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class CommunicationCategory(GenericNamedModel):
    class Meta(GenericNamedModel.Meta):
        verbose_name_plural = 'Communication categories'

    is_active = models.BooleanField(default=True)


class CommunicationStatus(GenericNamedModel):
    is_closed = models.BooleanField(default=False)

    class Meta(GenericNamedModel.Meta):
        verbose_name_plural = 'Communication statuses'


class CommunicationSubcategory(GenericNamedModel):
    category = models.ManyToManyField(
        CommunicationCategory, related_name='subcategories')

    class Meta(GenericNamedModel.Meta):
        verbose_name_plural = 'Communication subcategories'


class CommunicationResolution(GenericNamedModel):
    pass


class DeactivationReason(models.Model):
    reason = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('reason',)

    def __unicode__(self):
        return self.reason


class DeviceProblem(GenericNamedModel):
    pass


class GDriveNonConformityType(GenericNamedModel):
    pass


class MeterDisposition(GenericNamedModel):
    is_problem = models.BooleanField(default=True)


class OrderProblemCategory(GenericNamedModel):
    pass
