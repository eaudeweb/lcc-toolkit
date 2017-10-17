from rolepermissions.roles import AbstractUserRole


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
