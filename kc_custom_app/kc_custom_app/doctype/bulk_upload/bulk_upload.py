# Copyright (c) 2025, Kivu Choice and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class BulkUpload(Document):
    def before_submit(self):
        if self.type == "BK Local Bank Transfer":
            if self.bk_local_bank_transfer:
                for item in self.bk_local_bank_transfer:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
                        
        elif self.type == "I&M Local Bank Transfer":
            if self.im_local_bank_transfer:
                for item in self.im_local_bank_transfer:
                    p_entry = frappe.get_doc("Payment Entry", item.payment_reference)
                    if p_entry.docstatus==0:
                        p_entry.custom_cash_flow_period = self.cash_flow_period

                        p_entry.save()
                        p_entry.submit()
    
    @frappe.whitelist()        
    def get_pending_payments(self):
        pymnts_list = []
        self.bk_local_bank_transfer = []
        # self.im_local_bank_transfer = []


        draft_payments = frappe.db.get_all('Payment Entry', filters={
            'status': ['in', ['Draft']],
            'payment_type': 'Pay',
            "custom_upload_type": self.type
        }, fields=['name', 'party', 'paid_amount', 'party_bank_account', 'custom_upload_type', 'reference_no'])
        
        if draft_payments:
            for pymnt in draft_payments:
                if pymnt.get("custom_upload_type") in ["BK Local Bank Transfer", "I&M Local Bank Transfer"]:
                    if pymnt.get("party_bank_account"):
                        
                        bank = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'bank')
                        bank_account = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'bank_account_no')
                        # swift_code = frappe.db.get_value("Bank Account", {"name": pymnt.get("party_bank_account")}, 'custom_swift_code')
                        pymnt["bank_name"] = bank
                        pymnt["bank_account"] = bank_account
                        # pymnt["swift_code"] = swift_code
                        
                        if not pymnt in pymnts_list:
                            pymnts_list.append(pymnt)
                else:
                   if not pymnt in pymnts_list:
                        pymnts_list.append(pymnt) 
                        
        response_data = {
            'draft_payments': pymnts_list
        }
     
        frappe.response['message'] = response_data
        
    @frappe.whitelist()
    def download_report(self):   
        site_url = frappe.utils.get_url()      
        report_url = f"{site_url}/app/query-report/{self.get('type')} Bank Bulk Upload?parent={self.get('name')}"
        
        frappe.response['message'] = report_url







                        