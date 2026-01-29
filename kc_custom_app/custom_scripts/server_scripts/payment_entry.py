import frappe
from frappe.utils import today, flt

def on_submit(doc, method=None):
    if doc.payment_type == "Pay" and doc.references:
        adv_docname = ""
        for item in doc.references:
            if item.reference_doctype == "Purchase Order":
                # Ensure account is set (logic from your script)
                doc.paid_to = "530006 - Supplier Advances - KC"
                
                # Check for existing tracker
                adv_docname = frappe.db.exists("Advance Payment Entry", {"purchase_order": item.reference_name})
                
                if not adv_docname:
                    adv_docname = create_advance_tracker_entry(item.reference_name)
                
                if adv_docname:
                    update_tracker_with_payment(adv_docname, doc)

def create_advance_tracker_entry(po_name):
    po_doc = frappe.get_doc("Purchase Order", po_name)
    if po_doc.docstatus == 1:
        new_adv_doc = frappe.new_doc("Advance Payment Entry")
        new_adv_doc.purchase_order = po_doc.name
        new_adv_doc.purchase_order_date = po_doc.transaction_date
        new_adv_doc.date = today()
        new_adv_doc.purchase_order_type = po_doc.custom_type
        new_adv_doc.currency = po_doc.currency
        new_adv_doc.status = "New"
        new_adv_doc.amount = po_doc.grand_total
        new_adv_doc.base_amount = po_doc.base_grand_total
        new_adv_doc.insert(ignore_permissions=True)
        return new_adv_doc.name

def update_tracker_with_payment(adv_docname, doc):
    adv_doc = frappe.get_doc("Advance Payment Entry", adv_docname)
    existing_pymts = [i.payment_entry for i in adv_doc.get("payment_entries")]
    
    if doc.name not in existing_pymts:
        adv_doc.append("payment_entries", {
            "payment_entry": doc.name,
            "currency": "RWF",
            "exchange_rate": 1,
            "amount": doc.paid_amount,
            "base_amount": doc.base_paid_amount
        })
        adv_doc.save(ignore_permissions=True)