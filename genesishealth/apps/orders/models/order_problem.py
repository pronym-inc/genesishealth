from django.db import models
from django.utils.timezone import now


class OrderProblem(models.Model):
    order = models.ForeignKey('Order', related_name='problems', on_delete=models.CASCADE)
    category = models.ForeignKey(
        'dropdowns.OrderProblemCategory', related_name='+', on_delete=models.CASCADE)
    description = models.TextField()
    added_by = models.ForeignKey(
        'auth.User', null=True, related_name='order_problems', on_delete=models.SET_NULL)
    added_datetime = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        'auth.User', null=True, related_name='resolved_problems', on_delete=models.SET_NULL)
    resolved_datetime = models.DateTimeField(null=True)
    resolved_description = models.TextField()

    def resolve(self, description, resolved_by=None):
        self.resolved_by = resolved_by
        self.resolved_datetime = now()
        self.resolved_description = description
        self.is_resolved = True
        self.save()
