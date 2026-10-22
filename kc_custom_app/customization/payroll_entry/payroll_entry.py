import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry


class CustomPayrollEntry(PayrollEntry):
    @frappe.whitelist()
    def fill_employee_details(self):
        employees = self.get_emp_list()
        self.set("employees", [])

        if not employees:
            error_msg = _(
                "No employees found for the mentioned criteria:<br>Company: {0}<br> Currency: {1}<br>Payroll Payable Account: {2}"
            ).format(
                frappe.bold(self.company),
                frappe.bold(self.currency),
                frappe.bold(self.payroll_payable_account),
            )
            if self.branch:
                error_msg += "<br>" + _("Branch: {0}").format(frappe.bold(self.branch))
            if self.department:
                error_msg += "<br>" + _("Department: {0}").format(frappe.bold(self.department))
            if self.designation:
                error_msg += "<br>" + _("Designation: {0}").format(frappe.bold(self.designation))
            if self.start_date:
                error_msg += "<br>" + _("Start date: {0}").format(frappe.bold(self.start_date))
            if self.end_date:
                error_msg += "<br>" + _("End date: {0}").format(frappe.bold(self.end_date))
            frappe.throw(error_msg, title=_("No employees found"))

        self.set("employees", employees)
        self.number_of_employees = len(self.employees)
        self.update_employees_with_withheld_salaries()

        return self.get_employees_html() if hasattr(self, "get_employees_html") else None

    def get_emp_list(self):
        """Employees whose Employee.salary_currency matches this entry's currency,
        excluding anyone who already has a salary slip overlapping the period."""
        params = {
            "company": self.company,
            "timesheet": 1 if self.salary_slip_based_on_timesheet else 0,
            "currency": self.currency,
            "payroll_payable_account": self.payroll_payable_account,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "payroll_frequency": self.payroll_frequency,
        }

        cond = ""
        for field in ("branch", "department", "designation"):
            value = self.get(field)
            if value:
                cond += f" and t1.{field} = %({field})s"
                params[field] = value

        if self.payroll_frequency:
            cond += " and t3.payroll_frequency = %(payroll_frequency)s"

        return frappe.db.sql(
            """
            select distinct
                t1.name as employee, t1.employee_name, t1.department, t1.designation
            from `tabEmployee` t1
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
                and t1.date_of_joining <= %(end_date)s
                and (t1.relieving_date is null or t1.relieving_date >= %(start_date)s)
                and not exists (
                    select 1 from `tabSalary Slip` ss
                    where ss.employee = t1.name
                        and ss.docstatus != 2
                        and ss.start_date <= %(end_date)s
                        and ss.end_date >= %(start_date)s
                )
            """
            + cond
            + " order by t1.name",
            params,
            as_dict=True,
        )