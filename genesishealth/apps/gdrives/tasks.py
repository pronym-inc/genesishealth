from celery.task import task

@task
def send_register_update(device_id, is_register, in_date):
    from genesishealth.apps.gdrives.models import GDrive
    try:
        device = GDrive.objects.get(pk=device_id)
    except GDrive.DoesNotExist:
        return
    device.sendRegisterUpdate(is_register, in_date)