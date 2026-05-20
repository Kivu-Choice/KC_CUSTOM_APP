import frappe
from frappe import _

def on_submit(doc, method):
    # Define the specific stock entry types that require attachments
    required_types = [
        "Fish Transfer to LC",
        "Fish Received at LC",
        "Fish Transfer to Branch",
        "Fish Received at Branch",
        "Fish Return from Branch",
        "Fish Returned to LC",
        "Fish Transfer to Projects",
        "Fish Transfer to Traders"
    ]
    
    # Only enforce the rule if the document's type matches our list
    if doc.stock_entry_type in required_types:
        # Check if there are any attachments linked to the document
        attachments = frappe.get_all('File', filters={
            'attached_to_doctype': doc.doctype, 
            'attached_to_name': doc.name
        })
        
        if not attachments:
            frappe.throw(_("Please Attach a Reference Document before submitting."))