from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction

from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.gdrives.models import GDrive


class Command(BaseCommand):

    def move_users(self, users, group):
        for user in users:
            if user.is_patient():
                existing_group = user.patient_profile.get_group()
                if existing_group:
                    existing_group.remove_patient(user)
                # Move devices.
                for device in existing_group.gdrives.all():
                    device.group = group
                    device.save()
                group.add_patient(user)
                # Check to see if their company needs to be moved.
                user.patient_profile.created_by_group = group
                user.patient_profile.save()
                company = user.patient_profile.company
                if company and company.group != group:
                    company.group = group
                    company.save()
                    if company.payor:
                        company.payor.group = group
                        company.payor.save()
            else:
                user.professional_profile.parent_group = group
                user.professional_profile.save()

    @transaction.commit_manually
    def handle(self, commit=False, *args, **kwargs):
        print("Starting groups: %s" % GenesisGroup.objects.count())
        print("Starting users: %s" % User.objects.count())
        print("Starting GDrives: %s" % GDrive.objects.count())
        users = User.objects.filter(
            Q(last_name="Demo", first_name="Becky Patient") |
            Q(last_name="Demo", first_name="Christy Patient") |
            Q(last_name="Demo", first_name="Daisy Patient") |
            Q(last_name="Demo", first_name="Deanna Patient") |
            Q(last_name="Demo", first_name="Gwen Patient") |
            Q(last_name="Demo", first_name="Jane RN") |
            Q(last_name="Demo", first_name="Jeff Patient") |
            Q(last_name="Demo", first_name="Jill RN") |
            Q(last_name="Demo", first_name="Jimmy_Patient") |
            Q(last_name="Demo", first_name="Joanne") |
            Q(last_name="Demo", first_name="Jody RN") |
            Q(last_name="Demo", first_name="Joe Patient") |
            Q(last_name="Demo", first_name="John Patient") |
            Q(last_name="Demo", first_name="Keith Patient") |
            Q(last_name="Demo", first_name="Kelly Patient") |
            Q(last_name="Demo", first_name="Laura Patient") |
            Q(last_name="Demo", first_name="Lena Patient") |
            Q(last_name="Demo", first_name="MaryAnn Patient") |
            Q(last_name="Demo", first_name="Richard Patient") |
            Q(last_name="Demo", first_name="RN_Betty") |
            Q(last_name="Demo", first_name="Ron Admin") |
            Q(last_name="Demo", first_name="Sam Patient") |
            Q(last_name="Demo", first_name="Shelby Patient") |
            Q(last_name="Demo", first_name="Sue Patient") |
            Q(last_name="Demo", first_name="Susan Patient") |
            Q(last_name="Demo", first_name="Todd RN") |
            Q(last_name="Demo", first_name="Trina Patient") |
            Q(last_name="demo", first_name="wally_patient") |
            Q(last_name="Demo", first_name="Will patient")
        )

        group = GenesisGroup.objects.get(name="Demonstration Group")

        self.move_users(users, group)

        users = User.objects.filter(
            Q(last_name="Andrews Caregiver", first_name="Lena") |
            Q(last_name="Andrews", first_name="Lena") |
            Q(last_name="Christopher Admin", first_name="Ron") |
            Q(last_name="Christopher", first_name="Ron") |
            Q(last_name="Reynolds", first_name="Marissa")
        )

        group = GenesisGroup.objects.get(name="Genesis Test Group")

        self.move_users(users, group)

        delete_patients = User.objects.filter(
            Q(last_name="Anderson", first_name="Nurse") |
            Q(last_name="Anthony", first_name="Susan") |
            Q(last_name="Baksh", first_name="Lindsey") |
            Q(last_name="Bear", first_name="Meat") |
            Q(last_name="Beef", first_name="Meat") |
            Q(last_name="Beer", first_name="Meat") |
            Q(last_name="Cross Dr", first_name="J") |
            Q(last_name="Cross", first_name="Admin Jason") |
            Q(last_name="Cross", first_name="Jaybird") |
            Q(last_name="Darwin", first_name="Charles") |
            Q(last_name="DEMO1_LAST", first_name="DEMO1_FIRST") |
            Q(last_name="Genesis", first_name="Nurse") |
            Q(last_name="Gregg", first_name="Keith") |
            Q(last_name="Important", first_name="Mister") |
            Q(last_name="Jeff", first_name="Gregg") |
            Q(last_name="Jones", first_name="Mary Lee") |
            Q(last_name="Keezley", first_name="Grezzy") |
            Q(last_name="Keithley", first_name="Gregg") |
            Q(last_name="Keithley", first_name="Z") |
            Q(last_name="last name", first_name="first name") |
            Q(last_name="MCTZ", first_name="TZ") |
            Q(last_name="Meat", first_name="Mutton") |
            Q(last_name="Nurse", first_name="QA 3") |
            Q(last_name="Patient", first_name="Jason") |
            Q(last_name="Patient", first_name="Joe") |
            Q(last_name="Patient", first_name="Ken Demo") |
            Q(last_name="Professional", first_name="Test") |
            Q(last_name="Q", first_name="Kevin") |
            Q(last_name="Quinn", first_name="Kevin") |
            Q(last_name="Quinn", first_name="Kevin Admin") |
            Q(last_name="Quinn", first_name="Kevin_test") |
            Q(last_name="Ryan", first_name="Patrick") |
            Q(last_name="Storm", first_name="Susan") |
            Q(last_name="Super", first_name="K") |
            Q(last_name="Test", first_name="Frank Patient") |
            Q(last_name="Test", first_name="Rosie Nurse") |
            Q(last_name="Test", first_name="Steve Patient") |
            Q(last_name="Xavier", first_name="Charles") |
            Q(last_name="Zizek", first_name="Slavoj") |
            Q(last_name="Smith(&^&(&^*)YUK", first_name="John!@#$%^&*()") |
            Q(username="testverizonapiuser") |
            Q(username="VZTEST001") |
            Q(username="VZTEST002") |
            Q(username="VZTEST003") |
            Q(username="VZTEST004") |
            Q(username="VZTEST005") |
            Q(username="VZTEST006") |
            Q(username="VZTEST007") |
            Q(username="VZTEST008") |
            Q(username="VZTEST009") |
            Q(username="VZTEST010") |
            Q(username="VZTEST011") |
            Q(username="VZTEST012") |
            Q(username="VZTEST013") |
            Q(username="VZTEST014") |
            Q(username="VZTEST015") |
            Q(username="VZTEST016") |
            Q(username="VZTEST017") |
            Q(username="VZTEST018") |
            Q(username="VZTEST019") |
            Q(username="VZTEST020") |
            Q(username="VZTEST021")
        )

        delete_patients.delete()

        delete_groups = GenesisGroup.objects.filter(
            Q(name="45s Company") |
            Q(name="ACME Disease Management") |
            Q(name="Chronic Disease Management") |
            Q(name="December_Test_DMO") |
            Q(name="Karnak Disease MGT Demo") |
            Q(name="MCC-Texas") |
            Q(name="Name One") |
            Q(name="Name Two") |
            Q(name="Test Group") |
            Q(name="Demo Group") |
            Q(name="Verizon Test Group")
        )

        delete_groups.delete()

        print("Ending groups: %s" % GenesisGroup.objects.count())
        print("Ending users: %s" % User.objects.count())
        print("Ending GDrives: %s" % GDrive.objects.count())
        if commit:
            transaction.commit()
        else:
            transaction.rollback()
