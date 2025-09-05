import frappe
from frappe.utils import now_datetime, get_datetime, format_datetime, fmt_money, format_timedelta

FEATURE_FLAG = "kc_custom_app_notifications_feature_enabled"  # set to 1 in site_config.json

def _enabled() -> bool:
    return bool(frappe.conf.get(FEATURE_FLAG))

def _human_age(dt) -> str:
    return format_timedelta(now_datetime() - dt)

def _money(amount, currency) -> str:
    return fmt_money(amount, currency=currency)

def send_pending_po_digest(min_age_hours: int = 24):
    """
    Email a digest of POs that have been in a 'Pending Approval...' workflow_state
    for more than `min_age_hours`.
    """
    if not _enabled():
        return

    recipients = ["jmurengera@kivuchoice.com", "huwizera@kivuchoice.com"]
    if not recipients:
        # Nothing to do if we have nobody to notify
        return

    cutoff_secs = min_age_hours * 60 * 60
    now = now_datetime()

    # Pull candidate POs: still active, not cancelled/closed, in a pending approval state
    pos = frappe.get_all(
        "Purchase Order",
        filters={
            "docstatus": ["<", 2],
            "status": ["not in", ["Cancelled", "Closed"]],
            "workflow_state": ["like", "Pending Approval%"],
        },
        fields=[
            "name", "supplier", "grand_total", "currency",
            "owner", "modified", "transaction_date", "workflow_state"
        ],
        order_by="modified asc",
        limit_page_length=500
    )

    rows = []
    for po in pos:
        last_update = get_datetime(po.modified)
        age_secs = (now - last_update).total_seconds()
        if age_secs >= cutoff_secs:
            rows.append({
                "name": po.name,
                "supplier": po.supplier,
                "grand_total": po.grand_total,
                "currency": po.currency,
                "workflow_state": po.workflow_state,   # e.g., "Pending Approval (CFO)"
                "last_update": last_update,
                "age": _human_age(last_update),
                "owner": po.owner,
                "txn_date": po.transaction_date,
            })

    if not rows:
        return  # nothing to report

    # Build HTML table
    header = """
        <tr>
          <th align="left">PO</th>
          <th align="left">Supplier</th>
          <th align="right">Total</th>
          <th align="left">State</th>
          <th align="left">Waiting</th>
          <th align="left">Last Updated</th>
          <th align="left">Owner</th>
          <th align="left">Transaction Date</th>
        </tr>
    """

    def tr(r):
        return f"""
        <tr>
          <td><a href="{frappe.utils.get_link_to_form('Purchase Order', r['name'], label=r['name'])}">{r['name']}</a></td>
          <td>{frappe.utils.escape_html(r['supplier'] or '')}</td>
          <td align="right">{_money(r['grand_total'], r['currency'])}</td>
          <td>{frappe.utils.escape_html(r['workflow_state'])}</td>
          <td>{frappe.utils.escape_html(r['age'])}</td>
          <td>{format_datetime(r['last_update'])}</td>
          <td>{frappe.utils.escape_html(r['owner'])}</td>
          <td>{format_datetime(r['txn_date']) if r['txn_date'] else ''}</td>
        </tr>
        """

    body = f"""
    <p>Hi Procurement Manager,</p>
    <p>The following Purchase Orders have been in a pending approval state for more than <b>{min_age_hours} hours</b>.
    Please follow up with the indicated approver (e.g., CFO) as needed.</p>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
      {header}
      {''.join(tr(r) for r in rows)}
    </table>
    <p>Total pending > {min_age_hours}h: <b>{len(rows)}</b></p>
    """

    subject = f"[POs Pending >{min_age_hours}h] {len(rows)} approval(s) waiting — {frappe.utils.formatdate(now)}"

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=body,
        delayed=False,
        header=["PO Approvals", "orange"],
    )