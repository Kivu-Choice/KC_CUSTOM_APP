// Set the columns definition for the PPE Issue Summary Report
// This is used by the Report View to correctly display the data fetched by the Python script.
frappe.query_reports["PPE Issue Summary"] = {
	"filters": [
		// Note: Filters are defined in the .json file, but this is where we can add client-side logic.
	],
	"columns": [
		{
			"label": __("Employee"),
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