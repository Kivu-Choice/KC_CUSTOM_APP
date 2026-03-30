import frappe
from frappe.utils import (
    today, flt, get_year_ending, date_diff, 
    get_year_start, get_datetime, get_last_day
)

def auto_create_leave_allocation():
    """
    Daily scheduler task to process monthly accruals based on Date of Joining.
    Handles edge cases for months with fewer than 31 days.
    """
    curr_date = get_datetime(today())
    last_day_of_curr_month = get_last_day(today())
    is_last_day = (today() == last_day_of_curr_month)

    active_employees = frappe.db.get_all("Employee", 
        filters={"status": "Active"}, 
        fields=["name", "date_of_joining", "custom_job_level", "company"]
    )
    
    for emp in active_employees:
        if not emp.date_of_joining:
            continue
        
        if today() == emp.date_of_joining:
            # Handle first-day allocation for new joiners
            create_initial_zero_allocation(emp)
            continue
            
        doj = get_datetime(emp.date_of_joining)
        
        # Trigger accrual if:
        # 1. Today's date matches the joining day (e.g., 15th == 15th).
        # 2. It is the last day of a short month and the joining day is later in the month 
        #    (e.g., June 30th for a person who joined on the 31st).
        if curr_date.day == doj.day or (is_last_day and doj.day > curr_date.day):
            process_monthly_accrual(emp)

def get_leave_config(emp):
    """Determines Leave Type and Annual Cap based on Job Level and Tenure."""
    # 1. C&D Level Logic (Director/Chief)
    if emp.custom_job_level in ["Director", "Chief"]:
        return "Annual Leave C&D", 21.0
    
    # 2. Standard Tenure Logic
    years_worked = date_diff(today(), emp.date_of_joining) / 365.25
    
    if years_worked >= 10: annual_cap = 21.0
    elif years_worked >= 7: annual_cap = 20.0
    elif years_worked >= 4: annual_cap = 19.0
    else: annual_cap = 18.0
    
    return "Annual Leave", annual_cap

def process_monthly_accrual(emp):
    """Calculates monthly slice and updates Allocation + Ledger."""
    leave_type, annual_cap = get_leave_config(emp)
    month_name = get_datetime(today()).strftime("%B")
    
    # Monthly slice (e.g., 19 / 12 = 1.583333)
    monthly_rate = flt(annual_cap / 12, 6) 

    alloc_name = frappe.db.get_value("Leave Allocation", {
        "employee": emp.name, 
        "leave_type": leave_type, 
        "docstatus": 1,
        "from_date": ["<=", today()], 
        "to_date": [">=", today()]
    })

    if alloc_name:
        doc = frappe.get_doc("Leave Allocation", alloc_name)
        
        doc.total_leaves_allocated = flt(doc.total_leaves_allocated) + monthly_rate
        doc.new_leaves_allocated = flt(doc.new_leaves_allocated) + monthly_rate
        
        # Save the change to the Allocation document
        doc.db_update() 
        
        # Add Ledger Entry and SUBMIT it
        create_ledger_entry(doc, monthly_rate, f"Accrual: {month_name}")
        
        doc.add_comment("Comment", f"Accrued {flt(monthly_rate, 2)} days. New Total: {flt(doc.total_leaves_allocated, 2)}")
    else:
        year_start = get_year_start(today())
        year_end = get_year_ending(today())
        create_new_allocation(emp, leave_type, monthly_rate, year_start, year_end)

def create_new_allocation(emp, leave_type, rate, start, end):
    new_doc = frappe.new_doc("Leave Allocation")
    new_doc.update({
        "employee": emp.name, "leave_type": leave_type, "company": emp.company,
        "from_date": start, "to_date": end,
        "new_leaves_allocated": rate, "total_leaves_allocated": rate,
        "carry_forward": 1
    })
    new_doc.insert(ignore_permissions=True).submit()
    create_ledger_entry(new_doc, rate, "Initial Monthly Accrual")

def create_initial_zero_allocation(emp):
    leave_type, _ = get_leave_config(emp)
    if not frappe.db.exists("Leave Allocation", {"employee": emp.name, "leave_type": leave_type, "from_date": get_year_start(today())}):
        create_new_allocation(emp, leave_type, 0, get_year_start(today()), get_year_ending(today()))

def create_ledger_entry(doc, leaves, description):
    """Creates and Submits a Leave Ledger Entry to ensure report visibility."""
    ledger = frappe.new_doc("Leave Ledger Entry")
    ledger.update({
        "employee": doc.employee, 
        "leave_type": doc.leave_type,
        "transaction_type": "Leave Allocation", 
        "transaction_name": doc.name,
        "leaves": flt(leaves), 
        "from_date": today(), 
        "to_date": doc.to_date,
        "is_carry_forward": 0, 
        "remarks": description
    })
    
    ledger.flags.ignore_permissions = True
    ledger.flags.ignore_validate = True 
    
    ledger.insert()
    ledger.submit()