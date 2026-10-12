import frappe
from frappe.utils import flt, fmt_money
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip, get_salary_component_data
from hrms.payroll.doctype.additional_salary.additional_salary import get_additional_salaries

class CustomSalarySlip(SalarySlip):
    def get_data_for_eval(self):
        data, default_data = super().get_data_for_eval()

        foreign_base = flt(data.get("custom_foreign_base"))

        if foreign_base and self.exchange_rate:
            base = flt(foreign_base * flt(self.exchange_rate))
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
                additional_salary.amount *= self.exchange_rate
            self.update_component_row(
                get_salary_component_data(additional_salary.component),
                additional_salary.amount,
                component_type,
                additional_salary,
                is_recurring=additional_salary.is_recurring,
            )

def validate(self, method):
    update_foreign_currency(self)

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