from django.db import models


class PharmacyPartner(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, null=True)
    phone_number = models.CharField(max_length=255, null=True)
    epc_identifier = models.CharField(max_length=255, null=True, unique=True)

    def __unicode__(self):
        return self.name

    def get_full_address(self):
        output = self.address
        if self.address2:
            output += " / {0}".format(self.address2)
        return output
