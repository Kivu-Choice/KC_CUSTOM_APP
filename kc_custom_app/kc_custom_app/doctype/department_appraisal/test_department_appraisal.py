# Copyright (c) 2026, Kivu Choice and Contributors
# See license.txt

import frappe
from unittest.mock import patch, MagicMock
from frappe.tests.utils import FrappeTestCase
from kc_custom_app.kc_custom_app.doctype.department_appraisal.department_appraisal import DepartmentAppraisal


class TestDepartmentAppraisal(FrappeTestCase):
    def setUp(self):
        self.appraisal = DepartmentAppraisal(
            doctype="Department Appraisal",
            company='Test Company',
            department='Test Department',
        )

    def test_validate_duplicate_appraisal(self):
        with patch('frappe.db.get_all') as mock_get_all:
            mock_get_all.return_value = ['existing_appraisal']

            self.appraisal.company = 'Test Company'
            self.appraisal.department = 'Test Department'
            self.appraisal.appraisal_cycle = 'FY 2023-24'
            self.appraisal.docstatus = 0

            with self.assertRaises(frappe.ValidationError) as e:
                self.appraisal.validate()

            self.assertEqual(str(e.exception), "Appraisal existing_appraisal within the same appraisal cycle already exists.")

    def test_set_kras_with_appraisal_cycle(self):
        self.appraisal.appraisal_cycle = 'FY 2023-24'

        with patch('frappe.get_doc') as mock_get_doc:
            mock_template = MagicMock()
            mock_template.goals = [
                MagicMock(key_result_area='KRA 1', per_weightage=50),
                MagicMock(key_result_area='KRA 2', per_weightage=50),
            ]
            mock_get_doc.return_value = mock_template

            self.appraisal.set_kras()

            self.assertEqual(len(self.appraisal.goals), 2)
            self.assertEqual(self.appraisal.goals[0].get('kra'), 'KRA 1')
            self.assertEqual(self.appraisal.goals[0].get('per_weightage'), 50)
            self.assertEqual(self.appraisal.goals[1].get('kra'), 'KRA 2')
            self.assertEqual(self.appraisal.goals[1].get('per_weightage'), 50)


    def test_set_kras_without_appraisal_cycle(self):
            self.appraisal.set_kras()

            self.assertEqual(self.appraisal.goals, [])