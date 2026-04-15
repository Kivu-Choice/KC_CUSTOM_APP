# Copyright (c) 2026, Kivu Choice and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCompanyAppraisal(FrappeTestCase):
    def setUp(self):
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test Company",
            "default_currency": "USD",
        })
        company.insert()

        appraisal_cycle = frappe.get_doc({
            "doctype": "Appraisal Cycle",
            "cycle_name": "Test Cycle",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31"
        })
        appraisal_cycle.insert()


    def test_validate_duplicate_appraisal(self):
        company_appraisal = frappe.get_doc({
            "doctype": "Company Appraisal",
            "company": "Test Company",
            "appraisal_cycle": "Test Cycle",
            "score": 87
        })
        company_appraisal.insert()

        duplicate_appraisal = frappe.get_doc({
            "doctype": "Company Appraisal",
            "company": "Test Company",
            "appraisal_cycle": "Test Cycle",
        })

        # Attempt to save the duplicate appraisal
        with self.assertRaises(frappe.ValidationError) as context:
            duplicate_appraisal.insert()

        self.assertIn("Appraisal", str(context.exception))
        self.assertIn("within the same appraisal cycle already exists", str(context.exception))

    def tearDown(self):
        try:
            frappe.delete_doc("Company", "Test Company")
            frappe.delete_doc("Appraisal Cycle", "Test Cycle")
        except frappe.LinkExistsError as e:
            frappe.db.rollback()
            print(f"Error occurred during cleanup: {e}")
