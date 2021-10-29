from rolepermissions.roles import AbstractUserRole, RolesManager

# TODO: Decide on permissions for each role
# (or just use role-based checks on views?)
class SiteAdministrator(AbstractUserRole):
    role_name = "Site administrator"
    available_permissions = {}


class PolicyMaker(AbstractUserRole):
    role_name = "Policy maker"
    available_permissions = {}


class ContentManager(AbstractUserRole):
    role_name = "Content manager"
    available_permissions = {}


class Government(AbstractUserRole):
    role_name = "Government"
    available_permissions = {}


class Student(AbstractUserRole):
    role_name = "Student"
    available_permissions = {}


class InterGovernmentalOrganization(AbstractUserRole):
    role_name = "Inter-governmental organization"
    available_permissions = {}


class NonGovernmentalOrganization(AbstractUserRole):
    role_name = "Non-governmental organization"
    available_permissions = {}


class Researcher(AbstractUserRole):
    role_name = "Researcher"
    available_permissions = {}


class Academia(AbstractUserRole):
    role_name = "Academia"
    available_permissions = {}


class Other(AbstractUserRole):
    role_name = "Other"
    available_permissions = {}



def get_nonprivileged_roles():
    return [
        name
        for name in RolesManager.get_roles_names()
        if name != SiteAdministrator.get_name() and name != ContentManager.get_name()
    ]
