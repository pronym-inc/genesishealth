from celery.task import task


@task
def create_qa_log_entry(meid, reading_datetime, glucose_value):
    from genesishealth.apps.logs.models import QALogEntry
    QALogEntry.objects.create(
        meid=meid,
        reading_datetime=reading_datetime,
        glucose_value=glucose_value
    )
