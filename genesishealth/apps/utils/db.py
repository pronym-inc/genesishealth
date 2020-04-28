from django.db.models import Model

def reload_django_object(obj, manager_name='objects'):
    """If we have an instance of a Django object and want to see if its database status has changed, we have
    to manually reload it from the database.  This function returns a reloaded version of the provided obj."""
    if not isinstance(obj, Model):
        raise ValueError('reload_django_object only accepts Django models.')
    model_class = obj.__class__
    manager = getattr(model_class, manager_name)
    return manager.get(pk=obj.pk)