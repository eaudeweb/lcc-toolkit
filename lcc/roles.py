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


def get_nonprivileged_roles():
    return [
        name for name in RolesManager.get_roles_names()
        if name != SiteAdministrator.get_name()
            and name != ContentManager.get_name()
    ]
