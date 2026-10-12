from frappe.utils import flt

def validate(doc, method=None):
    if doc.get("custom_foreign_base") and doc.get("custom_exchange_rate"):
        doc.base = flt(doc.custom_foreign_base) * flt(doc.custom_exchange_rate)