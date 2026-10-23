import erpnext
import frappe
from frappe.utils import flt, fmt_money
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip, get_salary_component_data
from hrms.payroll.doctype.additional_salary.additional_salary import get_additional_salaries

class CustomSalarySlip(SalarySlip):
    def get_usd_rate(self):
        """Real conversion rate, read from the Payroll Entry, not from the slip."""
        if self.payroll_entry:
            rate = flt(frappe.db.get_value("Payroll Entry", self.payroll_entry, "exchange_rate"))
            if rate > 1:
                return rate
        return 1

    def get_data_for_eval(self):
        data, default_data = super().get_data_for_eval()

        foreign_base = flt(data.get("custom_foreign_base"))
        rate = self.get_usd_rate()

        if foreign_base and rate > 1:
            base = flt(foreign_base * rate)
            data["base"] = base
            default_data["base"] = base

        return data, default_data

    def add_additional_salary_components(self, component_type):
        additional_salaries = get_additional_salaries(
            self.employee, self.start_date, self.end_date, component_type
        )

        convertable_components = frappe.db.get_all(
            "Salary Component", {"custom_is_in_employee_currency": 1}, pluck="name"
        )

        for additional_salary in additional_salaries:
            if additional_salary.component in convertable_components:
                additional_salary.amount *= self.get_usd_rate()
            self.update_component_row(
                get_salary_component_data(additional_salary.component),
                additional_salary.amount,
                component_type,
                additional_salary,
                is_recurring=additional_salary.is_recurring,
            )

def validate(self, method):
    update_foreign_currency(self)
    sync_base_to_company_currency(self)
    self.exchange_rate = 1

def update_foreign_currency(self):
    if not self.payroll_entry:
        return

    exchange_rate = flt(frappe.db.get_value("Payroll Entry", self.payroll_entry, "exchange_rate"))
    if exchange_rate <= 1:
        return

    foreign_currency = frappe.db.get_value("Employee", self.employee, "salary_currency")

    for row in self.earnings + self.deductions:
        amount = row.amount or row.default_amount or row.additional_amount
        row.custom_foreign_amount = fmt_money(flt(amount / exchange_rate, 3), 2, foreign_currency)

    self.custom_foreign_gross_pay = fmt_money(flt(self.gross_pay / exchange_rate, 2), 2, foreign_currency)
    self.custom_foreign_total_deduction = fmt_money(flt(self.total_deduction / exchange_rate, 2), 2, foreign_currency)
    self.custom_foreign_net_pay = fmt_money(flt(self.net_pay / exchange_rate, 2), 2, foreign_currency)
    self.custom_foreign_rounded_total = fmt_money(flt(self.rounded_total / exchange_rate, 0), 2, foreign_currency)

def sync_base_to_company_currency(self):
    """Slip amounts are already in company currency, so base_* must equal them."""
    if self.currency != erpnext.get_company_currency(self.company):
        return

    for f in ("gross_pay", "total_deduction", "net_pay", "rounded_total"):
        if self.meta.has_field(f"base_{f}"):
            self.set(f"base_{f}", flt(self.get(f)))

    for row in self.earnings + self.deductions:
        for f in ("amount", "default_amount", "additional_amount", "year_to_date"):
            if row.meta.has_field(f"base_{f}"):
                row.set(f"base_{f}", flt(row.get(f)))