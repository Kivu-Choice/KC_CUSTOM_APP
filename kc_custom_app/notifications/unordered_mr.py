import frappe

def _enabled():
    return bool(frappe.conf.get("kc_custom_app_notifications_feature_enabled"))

def send_unordered_mr_digest(recipients=None):
    if not _enabled():
        return

    recipients = recipients or [
        "cnisingizwe@kivuchoice.com",
        "fiyibukiro@kivuchoice.com",
        "bkwisanga@kivuchoice.com",
        "jmurengera@kivuchoice.com"
    ]

    # Submitted, type=Purchase MRs with NO linked PO (Draft or Submitted).
    # We ignore canceled POs (docstatus=2).
    mrs = frappe.db.sql("""
        SELECT mr.name, mr.transaction_date, mr.owner
        FROM `tabMaterial Request` mr
        WHERE mr.docstatus = 1
          AND mr.material_request_type = 'Purchase'
          AND mr.status != 'Stopped'
          AND NOT EXISTS (
              SELECT 1
              FROM `tabPurchase Order Item` poi
              JOIN `tabPurchase Order` po ON po.name = poi.parent
              WHERE poi.material_request = mr.name
                AND po.docstatus IN (0, 1)  -- draft or submitted count as “has PO”
          )
        ORDER BY mr.transaction_date ASC
    """, as_dict=True)

    if not mrs:
            frappe.log_error(
                title="Unordered MR Digest",
                message="No submitted purchase-type Material Requests without a linked Purchase Order found."
            )
        return

    def row(m):
        url = frappe.utils.get_url_to_form("Material Request", m["name"])
        date = frappe.utils.formatdate(m["transaction_date"])
        age = frappe.utils.date_diff(frappe.utils.today(), m["transaction_date"])
        return f'<li><a href="{url}">{m["name"]}</a> — {date} ({age} day(s) old) — created by {m["owner"]}</li>'

    items_html = "".join(row(m) for m in mrs)
    message = (
        "Hello Procurement Team,<br><br>"
        "These <b>submitted</b> Material Requests (type: Purchase) have "
        "<b>no linked Purchase Orders</b> (Draft or Submitted):<br>"
        f"<ul>{items_html}</ul>"
        "<br>These requests are awaiting your action. Please initiate the Purchase Order (even as Draft) to start the procurement process."
    )

    subject = f"Unordered Material Requests (no POs) — {frappe.utils.formatdate(frappe.utils.today())}"
    frappe.sendmail(
        recipients=recipients,
        cc=["huwizera@kivuchoice.com"],
        subject=subject,
        message=message,
    )
