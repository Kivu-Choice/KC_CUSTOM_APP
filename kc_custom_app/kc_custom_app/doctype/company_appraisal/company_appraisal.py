# Copyright (c) 2026, Kivu Choice and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CompanyAppraisal(Document):
	def validate(self):
		appraisals = frappe.db.get_all('Company Appraisal', 
				filters = { 
					'company' : self.company,  
					'appraisal_cycle' : self.appraisal_cycle, 
					'docstatus' : ['<', 2], 
					'name': ['!=', self.name] 
				}, 
				pluck = 'name'
		)
		if appraisals:
			frappe.throw(f"Appraisal {appraisals[0]} within the same appraisal cycle already exists.")
