from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    # 1. Define the columns to be displayed in the report
    columns = get_columns()
    
    # 2. Build the main data query (Aggregated SQL)
    data = get_data(filters)
    
    # 3. Return the columns and the fetched data
    return columns, data

def get_columns():
    """Returns the list of columns for the report view."""
    return [
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 250},
        {"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 180},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": _("Last Issue Date"), "fieldname": "last_issue_date", "fieldtype": "Date", "width": 120},
        {"label": _("Total Quantity Issued"), "fieldname": "total_qty", "fieldtype": "Float", "width": 150},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 100},
    ]

def get_data(filters):
    """Fetches the aggregated material issue data based on filters."""
    
    query = """
        SELECT
            emp.employee_name,
            t1.custom_receiving_employee AS employee,
            t2.item_code,
            item.item_group,
            MAX(t1.posting_date) AS last_issue_date, -- NEW: Get the last issue date
            SUM(t2.qty) AS total_qty,
            t2.uom
        FROM
            `tabStock Entry` t1
        JOIN
            `tabStock Entry Detail` t2 ON t1.name = t2.parent
        JOIN
            `tabItem` item ON t2.item_code = item.name
        LEFT JOIN
            `tabEmployee` emp ON t1.custom_receiving_employee = emp.name
        WHERE
            t1.docstatus = 1 AND
            t1.stock_entry_type = 'Material Issue' AND
            t1.custom_receiving_employee IS NOT NULL
    """

    # List of values to be passed to the SQL query (for parameterized query)
    query_filters = []

    # 1. Apply Date Range Filter (mandatory from .json)
    if filters.get("posting_date"):
        start_date = filters["posting_date"][0]
        end_date = filters["posting_date"][1]
        query += " AND t1.posting_date BETWEEN %s AND %s"
        query_filters.extend([start_date, end_date])

    # 2. Apply Employee Filter (optional)
    if filters.get("employee"):
        query += " AND t1.custom_receiving_employee = %s"
        query_filters.append(filters["employee"])
        
    # 3. Apply Item Group Filter (optional)
    if filters.get("item_group"):
        query += " AND item.item_group = %s"
        query_filters.append(filters["item_group"])

    # 4. Group by Employee (on parent) and Item (on child) to get the summary
    # NOTE: posting_date is NOT included in GROUP BY as it is used with the MAX() aggregate function.
    query += " GROUP BY t1.custom_receiving_employee, t2.item_code, item.item_group, t2.uom"
    
    # Execute the query
    data = frappe.db.sql(query, tuple(query_filters), as_dict=1)
    
    return data