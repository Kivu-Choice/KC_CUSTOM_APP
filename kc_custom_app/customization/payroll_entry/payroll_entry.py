import frappe
from hrms.payroll.doctype.payroll_entry.payroll_entry import (
    PayrollEntry,
    get_filter_condition,
    get_joining_relieving_condition,
    remove_payrolled_employees,
)

class CustomPayrollEntry(PayrollEntry):
    def get_emp_list(self):
        """
        Employees for this Payroll Entry, matched on Employee.salary_currency
        == Payroll Entry currency. Everything else follows standard behaviour.
        """
        self.check_mandatory()
        filters = self.make_filters()

        cond = get_filter_condition(filters)
        cond += get_joining_relieving_condition(self.start_date, self.end_date)

        # Salary Structure conditions, minus the currency filter
        struct_cond = ""
        if self.payroll_frequency:
            struct_cond += " and t3.payroll_frequency = %(payroll_frequency)s"

        emp_list = frappe.db.sql(
            """
            select distinct
                t1.name as employee, t1.employee_name, t1.department, t1.designation
            from
                `tabEmployee` t1
                inner join `tabSalary Structure Assignment` t2 on t2.employee = t1.name
                inner join `tabSalary Structure` t3 on t3.name = t2.salary_structure
            where
                t2.docstatus = 1
                and t3.docstatus = 1
                and t3.is_active = 'Yes'
                and t3.company = %(company)s
                and t3.salary_slip_based_on_timesheet = %(timesheet)s
                and t1.status != 'Inactive'
                and t1.salary_currency = %(currency)s
                and t2.payroll_payable_account = %(payroll_payable_account)s
                and t2.from_date <= %(end_date)s
            """
            + struct_cond
            + " "
            + cond
            + " order by t1.name",
            {
                "company": self.company,
                "timesheet": self.salary_slip_based_on_timesheet,
                "currency": self.currency,
                "payroll_payable_account": self.payroll_payable_account,
                "end_date": self.end_date,
                "payroll_frequency": self.payroll_frequency,
            },
            as_dict=True,
        )

        return remove_payrolled_employees(emp_list, self.start_date, self.end_date)