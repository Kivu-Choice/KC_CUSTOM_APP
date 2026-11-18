# Copyright (c) 2026, Kivu Choice and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DepartmentAppraisal(Document):
    def validate(self):
        appraisals = frappe.db.get_all(
            "Department Appraisal",
            filters={
                "company": self.company,
                "department": self.department,
                "appraisal_cycle": self.appraisal_cycle,
                "docstatus": ["<", 2],
                "name": ["!=", self.name],
            },
            pluck="name",
        )
        if appraisals:
            frappe.throw(
                f"Appraisal {appraisals[0]} within the same appraisal cycle already exists."
            )

    @frappe.whitelist()
    def set_kras(self, parenttype="appraisal_template"):
        if not self.appraisal_cycle:
            return

        value = self.appraisal_template
        child_table = "goals"
        kra_key = "kra"
        score = "per_weightage"
        if parenttype != "appraisal_template":
            value = self.multiplier_template
            child_table = "appraisal_multiplier"
            kra_key = "template"
            score = "score"

        self.set(child_table, [])

        template = frappe.get_doc("Appraisal Template", value)

        for entry in template.goals:
            self.append(
                child_table,
                {
                    kra_key: entry.key_result_area,
                    score: entry.per_weightage if parenttype == "appraisal_template" else 0,
                },
            )

        return self

    def before_save(self):
        is_sys_manager = "System Manager" in frappe.get_roles()

        # Restrict edits to System Managers, listed approvers, and the document owner
        if not is_sys_manager:
            approvers = [row.approver for row in self.appraisal_approver if row.approver]
            if frappe.session.user not in approvers and frappe.session.user != self.owner:
                frappe.throw("You are not allowed to save/submit this appraisal")

        # Auto-check custom_approve when moving forward in the workflow
        if self.has_value_changed("workflow_state"):
            forward_states = [
                "Pending Approval (Director)",
                "Pending Approval (MD)",
                "Pending Approval (GCFO)",
                "Approved",
            ]

            if self.workflow_state in forward_states:
                for row in self.appraisal_approver:
                    if row.approver == frappe.session.user:
                        row.custom_approve = 1

            # Reset approvals if returned for amendment so the chain restarts cleanly
            elif self.workflow_state == "To Amend":
                for row in self.appraisal_approver:
                    row.custom_approve = 0

    def before_submit(self):
        if "System Manager" not in frappe.get_roles():
            for approver in self.appraisal_approver:
                if not approver.custom_approve:
                    frappe.throw(
                        f"Approval from <strong>{approver.approver}</strong> is still pending."
                    )

            last_approver = get_last_approver(self.appraisal_approver)
            if last_approver and frappe.session.user != last_approver:
                frappe.throw(
                    f"This appraisal can only be submitted by <strong>{last_approver}</strong>"
                )

    def on_update(self):
        # Only send notification emails when the workflow state moves into a Pending Approval state
        if self.has_value_changed("workflow_state") and self.workflow_state in [
            "Pending Approval (Director)",
            "Pending Approval (MD)",
            "Pending Approval (GCFO)",
        ]:
            send_emails_to_approver(self)


@frappe.whitelist()
def get_approvers(department=None):
    department_name = department or frappe.form_dict.get("department")
    if not department_name:
        return []

    user_list = []
    doc = frappe.get_doc("Department", department_name)
    approvers = doc.custom_appraisal_approvers
    if approvers:
        for approver in approvers:
            user = approver.get("approver")
            if user:
                user_list.append(user)

    return user_list


def send_emails_to_approver(doc):
    current_approver = get_approver_email(doc.appraisal_approver)
    if not current_approver:
        return

    template = doc.email_template or "Department Appraisal"
    send_mail(current_approver, template, doc)


def get_approver_email(approvers):
    for approver in approvers:
        if not approver.custom_approve:
            return approver.approver
    return None


def get_last_approver(approvers):
    if approvers:
        return approvers[-1].approver
    return None


def send_mail(email, template, appraisal_doc):
    if email is None:
        return

    email_template = frappe.get_doc("Email Template", template)
    context = {
        "name": appraisal_doc.name,
        "department": appraisal_doc.department,
        "total_goal_score": appraisal_doc.total_goal_score,
        "total_goal_score_percentage": appraisal_doc.total_goal_score_percentage,
    }

    try:
        frappe.sendmail(
            recipients=[email],
            subject="Appraisal Approval Request",
            message=frappe.render_template(
                email_template.response_html, context, is_path=False
            ),
        )
        frappe.msgprint(f"Email sent successfully to {email}")
    except Exception as e:
        frappe.throw(f"Error sending email: {e}")