import frappe
from frappe.model.document import Document
from frappe.utils import flt

class AdvancePaymentEntry(Document):
    def validate(self):
        """Recalculate totals every time the document is saved"""
        # Calculate Total Paid
        total_paid = sum(flt(i.base_amount) for i in self.get("payment_entries") if i.base_amount)
        self.total_paid_amount = total_paid
        
        # Calculate Total Invoiced
        total_invoiced = sum(flt(i.base_amount) for i in self.get("purchase_invoices") if i.base_amount)
        self.total_invoice_amount = total_invoiced
        
        # Calculate Remaining
        self.remaining_amount = flt(self.total_paid_amount) - flt(self.total_invoice_amount)

        # Update Status based on logic from your script
        if self.total_paid_amount > 0:
            if self.remaining_amount <= 1:
                self.status = "Fully Used"
            elif self.total_invoice_amount > 0:
                self.status = "Partially Used"