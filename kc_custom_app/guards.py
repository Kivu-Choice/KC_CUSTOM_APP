import frappe
from frappe import _

# protected role -> roles that may grant or revoke it
PROTECTED = {
    "Payroll Admin": {"Payroll Admin"},
    "Payroll Specialist": {"Payroll Admin"},
    "System Manager": {"System Manager"},
}

def _blocked(doc):
    before = doc.get_doc_before_save()
    old = {r.role for r in before.roles} if before else set()
    new = {r.role for r in doc.roles}
    user = frappe.session.user
    if user == "Administrator":
        return []
    mine = set(frappe.get_roles(user))
    return [role for role in (old ^ new) if role in PROTECTED and not (PROTECTED[role] & mine)]

def protect_payroll_role(doc, method=None):
    if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
        return
    blocked = _blocked(doc)
    if blocked:
        frappe.throw(_("You cannot assign or remove: {0}").format(", ".join(sorted(blocked))), frappe.PermissionError)

def protect_payroll_role_profile(doc, method=None):
    protect_payroll_role(doc, method)