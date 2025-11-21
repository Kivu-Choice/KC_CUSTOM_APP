// Copyright (c) 2025, Kivu Choice and contributors
// For license information, please see license.txt

frappe.query_reports["Procurement Tracker Lite"] = {
	"filters": [
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"default": frappe.defaults.get_user_default("Cost Center"),
			"reqd": 0,
			"width": "120"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date (MR)"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
			"width": "120"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date (MR)"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today(),
			"width": "120"
		}
	]
};