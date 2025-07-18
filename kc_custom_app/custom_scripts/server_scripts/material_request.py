import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    def set_header(source_doc, target_doc, source_parent=None):
        # now accepts the third arg without complaint
        if source_doc.get("custom_cost_center"):
            target_doc.cost_center = source_doc.custom_cost_center

    def map_item(source_item, target_item, source_parent=None):
        if source_parent and source_parent.get("custom_cost_center"):
            target_item.cost_center = source_parent.custom_cost_center

    return get_mapped_doc(
        "Material Request", source_name,
        {
            "Material Request": {
                "doctype": "Purchase Order",
                "postprocess": set_header,
                "validation": {"docstatus": ["=", 1]},
            },
            "Material Request Item": {
                "doctype": "Purchase Order Item",
                "field_map": {
                    "name":   "material_request_item",
                    "parent": "material_request",
                },
                "postprocess": map_item,
                "condition":  lambda d: d.qty - d.ordered_qty > 0,
            }
        },
        target_doc
    )