import frappe
from frappe import _

PROTECTED_ROLE = "Payroll Admin"

def _can_manage():
    user = frappe.session.user
    return user == "Administrator" or PROTECTED_ROLE in frappe.get_roles(user)

def protect_payroll_role(doc, method=None):
    if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
        return
    before = doc.get_doc_before_save()
    old = {r.role for r in before.roles} if before else set()
    new = {r.role for r in doc.roles}

    if PROTECTED_ROLE in (old ^ new) and not _can_manage():
        frappe.throw(_("Only Payroll Admins can assign or remove the {0} role.")
                     .format(PROTECTED_ROLE), frappe.PermissionError)

def protect_payroll_role_profile(doc, method=None):
    before = doc.get_doc_before_save()
    old = {r.role for r in before.roles} if before else set()
    new = {r.role for r in doc.roles}
    if PROTECTED_ROLE in (old ^ new) and not _can_manage():
        frappe.throw(_("You cannot add or remove {0} in a Role Profile.")
                     .format(PROTECTED_ROLE), frappe.PermissionError)