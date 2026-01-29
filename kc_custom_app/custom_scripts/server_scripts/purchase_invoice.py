import frappe
from frappe import _
from frappe.utils import flt

def on_submit(doc, method=None):
    # 1. Attachment Validation
    attachments = frappe.get_all('File', filters={'attached_to_doctype': doc.doctype, 'attached_to_name': doc.name})
    if not attachments:
        frappe.throw(_("Please Attach a Reference Document."))

    # 2. Advance Allocation
    if doc.items:
        advances_exist = ""
        for item in doc.items:
            if item.purchase_order and item.purchase_receipt:
                advances_exist = frappe.db.exists("Advance Payment Entry", {"purchase_order": item.purchase_order})
                if advances_exist:
                    break
        
        if advances_exist:
            adv_doc = frappe.get_doc("Advance Payment Entry", advances_exist)
            if adv_doc.remaining_amount > 1:
                create_payment_entry_from_advance(doc, adv_doc)
                
                # Link invoice to tracker
                existing_invoices = [i.purchase_invoice for i in adv_doc.get("purchase_invoices")]
                if doc.name not in existing_invoices:
                    adv_doc.append("purchase_invoices", {
                        "purchase_invoice": doc.name,
                        "currency": doc.currency,
                        "exchange_rate": 1,
                        "amount": doc.outstanding_amount,
                        "base_amount": doc.base_grand_total
                    })
                    adv_doc.save(ignore_permissions=True)

def create_payment_entry_from_advance(doc, adv_doc):
    # Use Mode of Payment from the first payment in the tracker to avoid hardcoding
    mop = "BK Local Sales" # Default
    if adv_doc.payment_entries:
        first_pe = frappe.get_value("Payment Entry", adv_doc.payment_entries[0].payment_entry, "mode_of_payment")
        if first_pe: mop = first_pe

    paid_amount = min(adv_doc.remaining_amount, doc.outstanding_amount)
    
    new_pe = frappe.new_doc("Payment Entry")
    new_pe.company = doc.company
    new_pe.payment_type = "Pay"
    new_pe.party_type = "Supplier"
    new_pe.party = doc.supplier
    new_pe.posting_date = doc.posting_date
    new_pe.mode_of_payment = mop
    new_pe.paid_from = "530006 - Supplier Advances - KC"
    new_pe.paid_to = "710001 - Trade Payables - KC"
    new_pe.paid_amount = paid_amount
    new_pe.received_amount = paid_amount
    new_pe.reference_no = adv_doc.purchase_order
    
    new_pe.append("references", {
        "reference_doctype": "Purchase Invoice",
        "reference_name": doc.name,
        "total_amount": doc.outstanding_amount,
        "allocated_amount": paid_amount
    })
    new_pe.insert(ignore_permissions=True)
    new_pe.submit()