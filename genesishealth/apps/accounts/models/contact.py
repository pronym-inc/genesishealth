from django.db import models


class Contact(models.Model):
    """
    General contact model
    """
    salutation = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    middle_initial = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        app_label = 'accounts'

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def add_phone(self, phone, **kwargs):
        PhoneNumber.objects.create(phone=phone, contact=self, **kwargs)

    def get_full_address(self):
        return "%s%s" % (
            self.address1,
            "/ %s" % self.address2 if self.address2 else '')

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def cell_phone(self):
        try:
            return self.phonenumber_set.filter(is_cell=True)[0].phone
        except IndexError:
            return ''
    cell_phone = property(cell_phone)

    def set_phone(self, new_phone):
        self.phonenumber_set.all().delete()
        self.add_phone(new_phone)

    def phone(self):
        try:
            return self.phonenumber_set.filter(is_contact=True)[0].phone
        except IndexError:
            try:
                return self.phonenumber_set.filter()[0].phone
            except IndexError:
                return ''
    phone = property(phone)


class PhoneNumber(models.Model):
    """
    Phone model to allow Contact to have multiple phone numbers
    """
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255)
    is_cell = models.BooleanField(default=False)
    is_contact = models.BooleanField(default=False)

    class Meta:
        app_label = 'accounts'
