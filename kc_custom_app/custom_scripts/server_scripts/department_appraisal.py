import frappe
from frappe import _

def validate(doc, method):
    """
    Prevents transitioning Department Appraisal out of Draft if no file is attached.
    """
    # Check if workflow_state is changing from Draft to a Pending Approval state
    if doc.has_value_changed("workflow_state"):
        prev_doc = doc.get_doc_before_save()
        prev_state = prev_doc.workflow_state if prev_doc else "Draft"
        
        if prev_state == "Draft" and doc.workflow_state in [
            "Pending Approval (Director)", 
            "Pending Approval (MD)"
        ]:
            attachments = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": doc.doctype,
                    "attached_to_name": doc.name
                },
                limit=1
            )
            
            if not attachments:
                frappe.throw(
                    _("Please attach the required appraisal supporting documents before sending for approval.")
                )