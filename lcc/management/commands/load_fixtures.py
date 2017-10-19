import lcc.constants as lcc_constants
import lcc.models as lcc_models

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):

    help = "Load initial data"

    FIXTURES = ("TaxonomyTagGroup", "TaxonomyTag",
                "TaxonomyClassification", "Countries", "Legislation")

    def load_user_profile_roles(self):
        for user_role_name in lcc_constants.USER_PROFILE_ROLES:
            print("Importing user role: %s" % user_role_name)
            lcc_models.UserRole(name=user_role_name).save()

    def handle(self, *args, **options):
        for fixture in Command.FIXTURES:
            call_command('loaddata', fixture)
        self.load_user_profile_roles()
