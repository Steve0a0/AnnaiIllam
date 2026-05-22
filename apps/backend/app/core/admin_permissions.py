from enum import Enum


class AdminPermissionGroup(str, Enum):
    SUPER_ADMIN = "super_admin"
    OPERATIONS = "operations_admin"
    FINANCE = "finance_admin"
    PAYROLL = "payroll_admin"
    SUPPORT = "support_admin"


ROUTE_PERMISSION_GROUPS = {
    "admin_requirements": AdminPermissionGroup.OPERATIONS.value,
    "admin_assignments": AdminPermissionGroup.OPERATIONS.value,
    "admin_attendance": AdminPermissionGroup.OPERATIONS.value,
    "admin_payroll": AdminPermissionGroup.PAYROLL.value,
    "admin_finance": AdminPermissionGroup.FINANCE.value,
    "admin_complaints": AdminPermissionGroup.SUPPORT.value,
    "admin_replacements": AdminPermissionGroup.SUPPORT.value,
    "admin_dashboard": AdminPermissionGroup.SUPER_ADMIN.value,
    "admin_reports": AdminPermissionGroup.SUPER_ADMIN.value,
}
