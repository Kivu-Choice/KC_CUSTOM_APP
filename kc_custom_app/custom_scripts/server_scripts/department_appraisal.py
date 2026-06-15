import frappe
from frappe import _

def on_submit(doc, method):
    """
    Prevents submission of Department Appraisal if no file is attached.
    """
    # Look for any file attached to this specific record
    attachments = frappe.get_all(
        'File', 
        filters={
            'attached_to_doctype': doc.doctype, 
            'attached_to_name': doc.name
        }
    )
    
    if not attachments:
        frappe.throw(_("Please attach the required appraisal supporting documents before submitting."))