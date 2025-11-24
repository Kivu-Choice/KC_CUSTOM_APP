# Copyright (c) 2025, Kivu Choice and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters) 
    return columns, data

def get_columns():
    columns = [
        {
            "label": _("Purchase Order ID"),
            "options": "Purchase Order",
            "fieldname": "po_name",
            "fieldtype": "Link",
            "width": 140,
        },
        {
            "label": _("PO Date"),
            "fieldname": "po_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Material Request ID"),
            "options": "Material Request",
            "fieldname": "mr_name",
            "fieldtype": "Link",
            "width": 140,
        },
        {
            "label": _("Material Request Date"),
            "fieldname": "mr_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Requester"),
            "options": "User",
            "fieldname": "requester",
            "fieldtype": "Link",
            "width": 120,
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
        },
        {"label": _("Quantity"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {
            "label": _("UOM"),
            "options": "UOM",
            "fieldname": "uom",
            "fieldtype": "Link",
            "width": 100,
        },
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": _("PO Amount"), "fieldname": "po_amount", "fieldtype": "Currency", "width": 120},
        {
            "label": _("Cost Center"),
            "options": "Cost Center",
            "fieldname": "cost_center",
            "fieldtype": "Link",
            "width": 140,
        },
    ]
    return columns


def get_data(filters):
    conditions = ["mr.docstatus = 1"]
    
    # Add filters based on user input
    if filters.get("cost_center"):
        # Filter on the Cost Center of the Material Request Item
        conditions.append(f"mri.cost_center = {frappe.db.escape(filters.get('cost_center'))}")

    if filters.get("from_date"):
        # Filter Material Request Date (mr.transaction_date) >= From Date
        conditions.append(f"mr.transaction_date >= {frappe.db.escape(filters.get('from_date'))}")

    if filters.get("to_date"):
        # Filter Material Request Date (mr.transaction_date) <= To Date
        conditions.append(f"mr.transaction_date <= {frappe.db.escape(filters.get('to_date'))}")

    # Combine all conditions
    where_clause = " AND ".join(conditions)


    query = f"""
        SELECT
            po.name AS po_name,
            po.transaction_date AS po_date,
            mr.name AS mr_name,
            mr.transaction_date AS mr_date,
            mr.owner AS requester,
            mri.item_code,
            mri.qty,
            mri.uom,
            mr.status,
            po.grand_total AS po_amount,
            mri.cost_center
        FROM `tabMaterial Request Item` mri
        JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        
        -- LEFT JOIN to Purchase Order Item (poi) and Purchase Order (po)
        LEFT JOIN `tabPurchase Order Item` poi ON poi.material_request_item = mri.name
        LEFT JOIN `tabPurchase Order` po ON po.name = poi.parent
        
        -- 3. APPLY FILTERS HERE
        WHERE {where_clause}
        ORDER BY mr.transaction_date DESC
    """
    
    data = frappe.db.sql(query, as_dict=True)

    # Post-process data to set the status correctly for items without a PO
    for row in data:
        if not row.po_name:
            # If there is no PO, PO-related fields are NULL.
            row.po_name = None
            row.po_date = None
            row.status = row.status 
            row.po_amount = 0
        else:
            # If a PO exists, use the PO status (which we pulled from po.status in the query)
            row.status = row.status

    return data