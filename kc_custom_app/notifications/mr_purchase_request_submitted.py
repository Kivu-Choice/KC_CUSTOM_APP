import frappe

FEATURE_FLAG_KEY = "kc_custom_app_notifications_feature_enabled"

# recipient email -> greeting name
RECIPIENT_NAME = {
    "bkwisanga@kivuchoice.com": "Brice",
    "cnisingizwe@kivuchoice.com": "Charite",
    "fiyibukiro@kivuchoice.com": "Fred",
    "inimuhoze@kivuchoice.com": "Immaculee"
}

CC_TO_RECIPIENT = {}

# bkwisanga@kivuchoice.com
for cc in [
    "204003 - Kagano Construction - KC",
    "204010 - Maintenance - KC",
    "204013 - Mwaga Construction - KC",
    "204014 - Kigembe Hatchery Construction - KC",
]:
    CC_TO_RECIPIENT[cc] = "bkwisanga@kivuchoice.com"

# cnisingizwe@kivuchoice.com
for cc in [
    "101005 - Pond Feeding - KC",
    "102003 - Inshore Lake Feeding - KC",
    "102004 - Offshore Lake Feeding - KC",
    "102011 - Lake Operations Feed Stores - KC",
]:
    CC_TO_RECIPIENT[cc] = "cnisingizwe@kivuchoice.com"

# fiyibukiro@kivuchoice.com
for cc in [
    "101001 - HERO Program - KC",
    "101002 - Incubation - KC",
    "101003 - Egg Collection - KC",
    "101004 - Pond Environment - KC",
    "101006 - Pond Fish Handling - KC",
    "101007 - Broodstock - KC",
    "101008 - Hatchery Ops - KC",
    "102001 - Production Planning and Reporting - KC",
    "102005 - Lake Operations Divers - KC",
    "102007 - Net Exchange and Cage Maintenance - KC",
    "102008 - Lake Environment and Data - KC",
    "102009 - Lake Operations Harvesting - KC",
    "102010 - Lake Operations Grading - KC",
    "102002 - Cage Mooring - KC",
    "102012 - Fish Health - KC",
    "103001 - Processing - KC",
    "103002 - Quality Assurance - KC",
    "204001 - Boats and Distribution - KC",
    "204002 - Circular Economy - Waste Management - KC",
    "204004 - Farm Fleet Land Based - KC",
    "204005 - Farm Administration - KC",
    "204006 - Farm Warehouse - KC",
    "204007 - Groundskeeping - KC",
    "204008 - Health and Safety - KC",
    "204009 - HouseKeeping - KC",
    "204011 - Net Fabrication and Weaving - KC",
    "204012 - Farm Security - KC",
]:
    CC_TO_RECIPIENT[cc] = "fiyibukiro@kivuchoice.com"

# inimuhoze@kivuchoice.com
for cc in [
    "305001 - Kigali LC - KC",
    "305002 - Kamembe LC - KC",
    "305004 - Farm LC - KC",
    "305003 - Gisenyi LC - KC",
    "406001 - Commercial Management - KC",
    "406002 - Marketing - KC",
    "406019 - HORECA Sales - KC",
    "409013 - Kamembe Town - KC",
    "409015 - Mobile Branch 1 - KC",
    "409016 - Mobile Branch 2 - KC",
    "409014 - Rusizi 1 - KC",
    "409012 - Rwesero - KC",
    "409011 - Tyazo - KC",
    "409023 - Rubavu Town - KC",
    "407003 - Kabuga Branch - KC",
    "407001 - Kiyovu Branch - KC",
    "407002 - Nyabugogo Branch - KC",
    "407004 - Nyamirambo Branch - KC",
    "407005 - Gikondo Branch - KC",
    "407020 - Kanombe Branch - KC",
    "408010 - Kimironko Branch - KC",
    "408009 - Ziniya Branch - KC",
    "408008 - Remera-Giporoso Branch - KC",
    "408006 - Batsinda Branch - KC",
    "408021 - Gisozi Branch - KC",
    "408022 - Gatenga Branch - KC",
    "410017 - Bukavu Traders - KC",
    "410018 - Gisenyi Traders - KC",
    "512001 - Community Relations - KC",
    "512002 - Reforestation - KC",
    "512003 - Fish Powder - KC",
    "511001 - Corporate Affairs - KC",
    "511002 - Executive - KC",
    "511003 - Finance - KC",
    "511004 - Human Resources - KC",
    "511005 - Administration - KC",
    "511006 - Procurement - KC",
    "511007 - Strategy and Operations - KC",
    "511008 - Information Technology - KC",
]:
    CC_TO_RECIPIENT[cc] = "inimuhoze@kivuchoice.com"


def _enabled() -> bool:
    return bool(frappe.conf.get(FEATURE_FLAG_KEY))


def send_material_request_purchase_submitted_notification(doc, method=None):
    """Hook on Material Request -> on_submit. Only for Purchase requests."""
    if not _enabled():
        return

    # only for Purchase
    if (getattr(doc, "material_request_type", None) or "").strip() != "Purchase":
        return

    try:
        cc = getattr(doc, "custom_cost_center", None)
        if not cc:
            frappe.log_error(
                title="MR Purchase Submitted Notification",
                message=f"Material Request {doc.name} has no doc.custom_cost_center",
            )
            return

        recipient = CC_TO_RECIPIENT.get(cc)
        if not recipient:
            frappe.log_error(
                title="MR Purchase Submitted Notification",
                message=f"No recipient mapping for cost center '{cc}' on MR {doc.name}",
            )
            return

        greet_name = RECIPIENT_NAME.get(recipient) or recipient
        url = frappe.utils.get_url_to_form(doc.doctype, doc.name)
        owner_name = frappe.db.get_value("User", doc.owner, "full_name") or doc.owner

        attachments = []
        try:
            pdf_attachment = frappe.attach_print(
                doctype=doc.doctype,
                name=doc.name,
                file_name=f"{doc.name}",
                print_format="Material Request",
                print_letterhead=True,
            )
            attachments = [pdf_attachment]
        except Exception as e:
            frappe.log_error(
                title="MR Purchase Submitted Notification (PDF attach failed)",
                message=f"Material Request {doc.name}: {e}",
            )

        frappe.sendmail(
            recipients=[recipient],
            cc=["huwizera@kivuchoice.com"],
            subject=f"Material Request (Purchase) Created: {doc.name}",
            message=(
                f"Hello {frappe.utils.escape_html(greet_name)},<br><br>"
                f"A <b>Material Request for Purchase</b> has been created and is ready for processing.<br>"
                f"Please get started on creating the <b>Purchase Order</b> for this request.<br><br>"
                f"<b>Material Request:</b> <a href=\"{url}\">{doc.name}</a><br>"
                f"<b>Cost Center:</b> {frappe.utils.escape_html(cc)}<br><br>"
                f"Best regards,<br>Kivu Choice Limited<br>"
            ),
            now=True,
            attachments=attachments,
        )


    except Exception as e:
        frappe.log_error(
            title="MR Purchase Submitted Notification (Fatal)",
            message=f"Material Request {doc.name}: {e}",
        )
