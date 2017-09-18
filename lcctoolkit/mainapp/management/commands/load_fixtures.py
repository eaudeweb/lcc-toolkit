import lcctoolkit.mainapp.constants as mainapp_constants
import lcctoolkit.mainapp.models as mainapp_models

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):

    help = "Load initial data"

    FIXTURES = ("TaxonomyTagGroup", "TaxonomyTag",
                "TaxonomyClassification", "Countries", "Legislation")

    def load_user_profile_roles(self):
        for user_role_name in mainapp_constants.USER_PROFILE_ROLES:
            print("Importing user role: %s" % user_role_name)
            mainapp_models.UserRole(name=user_role_name).save()

    def handle(self, *args, **options):
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
        self.load_user_profile_roles()
