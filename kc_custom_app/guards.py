"""
kc_custom_app/guards.py
=======================

PURPOSE
-------
Protects employee salary and payroll data from being exposed through
role or permission changes, even by users who hold broad admin roles such as
System Manager or HR Manager.

Access to payroll data is controlled by the "Payroll Admin" role, which is held
by only three people (Full Stack Engineer, HR Ops Manager, Finance Director, and Managing Director).
Permissions alone are not enough, because anyone who can assign roles or edit permissions could
give themselves or others access. These guards close those routes.

WHAT IT PROTECTS
----------------
Part 1: Role assignment
    Only authorised roles can grant or revoke sensitive roles on a User or
    Role Profile:
      - Payroll Admin      -> only Payroll Admins
      - Payroll Specialist -> only Payroll Admins
      - System Manager     -> only System Managers
    All other roles can still be assigned normally by System Managers or HR.

Part 2: Role Permissions Manager
    Adding, changing, removing or resetting permission rules on payroll
    doctypes requires Payroll Admin. Other doctypes are unaffected.

Part 3: Direct permission edits and Customize Form
    Blocks the side doors: editing Custom DocPerm records directly, and
    changing fields or properties (such as a field's Permission Level) on
    payroll doctypes through Custom Field and Property Setter.

HOW IT IS WIRED
---------------
Hooked up in hooks.py via `doc_events` (Parts 1 and 3) and
`override_whitelisted_methods` (Part 2). Removing those entries disables the
guards, so hooks.py and this file are listed in CODEOWNERS and covered by a test.

KNOWN LIMITS
------------
These are application-level guards. They do NOT stop the following, which
bypass doc events and permission rules entirely and can therefore read payroll
data:
  - Direct database / bench console access: full, unrestricted access.
  - System Manager: can read payroll tables through the System Console (SQL),
    Data Export, and any route not covered by the guards above.
  - Script Manager (anyone who can create Server Scripts): a Server Script runs
    Python with database access, so it can read salary tables regardless of
    permissions. Same applies to Query Reports and Script Reports.
  - Administrator, which is exempt on purpose so you can never be locked out.

Treat DB access, System Manager and Script Manager as equivalent to Payroll
Admin in terms of exposure. Mitigation:
  - Keep System Manager and Script Manager to the dev only (one or two trusted
    people), and require 2FA for them.
  - Restrict who can create Reports and use the System Console.
  - Limit Frappe Cloud dashboard / database access to the dev and owner.

MAINTENANCE
-----------
  - To protect another doctype, add it to PAYROLL_DOCTYPES.
  - To protect another role, add it to PROTECTED with the roles allowed to
    grant it.
  - Migrations, patches and installs are skipped so deployments never break.
"""

import frappe
from frappe import _
from frappe.core.page.permission_manager import permission_manager as pm

# ---------------------------------------------------------------
# Part 1: protect who can grant or revoke sensitive roles
# ---------------------------------------------------------------

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
        frappe.throw(
            _("You cannot assign or remove: {0}").format(", ".join(sorted(blocked))),
            frappe.PermissionError,
        )


def protect_payroll_role_profile(doc, method=None):
    protect_payroll_role(doc, method)


# ---------------------------------------------------------------
# Part 2: protect the Role Permissions Manager for payroll doctypes
# ---------------------------------------------------------------

PAYROLL_DOCTYPES = {
    "Salary Slip", "Salary Structure", "Salary Structure Assignment", "Payroll Entry",
    "Additional Salary", "Salary Component", "Payroll Period", "Income Tax Slab",
    "Employee Incentive", "Retention Bonus",
}
PERMISSION_EDITORS = {"Payroll Admin"}


def _check_payroll_perm_edit(doctype):
    if doctype not in PAYROLL_DOCTYPES or frappe.session.user == "Administrator":
        return
    if not (PERMISSION_EDITORS & set(frappe.get_roles())):
        frappe.throw(
            _("Only Payroll Admins can change permissions on {0}").format(doctype),
            frappe.PermissionError,
        )


@frappe.whitelist()
def pm_add(parent, role, permlevel):
    _check_payroll_perm_edit(parent)
    return pm.add(parent, role, permlevel)


@frappe.whitelist()
def pm_update(doctype, role, permlevel, ptype, value=None, if_owner=0):
    _check_payroll_perm_edit(doctype)
    return pm.update(doctype, role, permlevel, ptype, value, if_owner)


@frappe.whitelist()
def pm_remove(doctype, role, permlevel, if_owner=0):
    _check_payroll_perm_edit(doctype)
    return pm.remove(doctype, role, permlevel, if_owner)


@frappe.whitelist()
def pm_reset(doctype):
    _check_payroll_perm_edit(doctype)
    return pm.reset(doctype)


# ---------------------------------------------------------------
# Part 3: protect direct permission edits and Customize Form
# ---------------------------------------------------------------

def _guard_payroll_doctype(doctype):
    if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
        return
    _check_payroll_perm_edit(doctype)


def protect_custom_docperm(doc, method=None):
    _guard_payroll_doctype(doc.parent)


def protect_custom_field(doc, method=None):
    _guard_payroll_doctype(doc.dt)


def protect_property_setter(doc, method=None):
    # Property Setters can also target non-doctype records, so only payroll doctypes are checked
    _guard_payroll_doctype(doc.doc_type)