// Set the columns definition for the Employee Material Issue Summary Report
frappe.query_reports["Employee Material Issue Summary"] = {
    "filters": [
        // Note: Filters are defined in the .json file, but this is where we can add client-side logic.
    ],
    "columns": [
        {
            "label": __("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 250
        },
        {
            "label": __("Employee ID"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "label": __("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 180
        },
        {
            "label": __("Item Group"), 
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 150
        },
        {
            "label": __("Last Issue Date"),
            "fieldname": "last_issue_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": __("Total Quantity Issued"),
            "fieldname": "total_qty",
            "fieldtype": "Float",
            "width": 150,
            "precision": 3
        },
        {
            "label": __("UOM"),
            "fieldname": "uom",
            "fieldtype": "Link",
            "options": "UOM",
            "width": 100
        },
    ],
};