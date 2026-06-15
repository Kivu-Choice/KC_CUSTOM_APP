import frappe
from frappe.utils import today, add_days, format_datetime, get_link_to_form

FEATURE_FLAG = "kc_custom_app_notifications_feature_enabled"

REGIONS = {
    "Kigali East": ["Kimironko - KC", "Remera-Giporoso - KC", "Kabuga - KC", "Kanombe - KC"],
    "Kigali Central": ["Kiyovu - KC", "Gikondo - KC", "Gatenga - KC", "Ziniya - KC"],
    "Kigali West": ["Batsinda - KC", "Gisozi - KC", "Nyabugogo - KC", "Nyamirambo - KC"],
    "Kivu Belt": ["Rusizi 1 - KC", "Kamembe Town - KC", "Rwesero - KC", "Tyazo - KC", "Mobile Branch - KC", "Rubavu Town - KC"]
}

def _enabled() -> bool:
    return bool(frappe.conf.get(FEATURE_FLAG))

def send_daily_fish_received_digest():
    """
    Daily digest summarizing 'Fish Received at Branch' Stock Entries for YESTERDAY.
    Runs via hooks Scheduler configuration.
    """
    if not _enabled():
        return

    # Updated Recipients
    recipients = ["dbyiringiro@kivuchoice.com", "huwizera@kivuchoice.com"]
    if not recipients:
        return

    # Evaluates entries logged yesterday
    target_date = add_days(today(), -1)
    
    # Pull all matching stock entries for yesterday
    entries = frappe.get_all(
        "Stock Entry",
        filters={
            "stock_entry_type": "Fish Received at Branch",
            "posting_date": target_date
        },
        fields=["name", "to_warehouse", "docstatus", "creation"]
    )

    entry_map = {e["to_warehouse"]: e for e in entries if e["to_warehouse"]}

    def get_status_badge(docstatus):
        if docstatus == 0:
            return '<span style="color: #d97706; font-weight: bold;">Draft</span>'
        elif docstatus == 1:
            return '<span style="color: #16a34a; font-weight: bold;">Submitted</span>'
        return '<span style="color: #dc2626; font-weight: bold;">Cancelled</span>'

    html_tables = ""
    for region_name, warehouses in REGIONS.items():
        table_rows = ""
        for wh in warehouses:
            entry = entry_map.get(wh)
            if entry:
                status_text = get_status_badge(entry["docstatus"])
                url = get_link_to_form("Stock Entry", entry["name"])
                doc_link = f'<a href="{url}">{entry["name"]}</a>'
                created_time = format_datetime(entry["creation"], "hh:mm AT")
            else:
                status_text = '<span style="color: #ef4444; font-style: italic;">No Entry Found</span>'
                doc_link = "-"
                created_time = "-"

            table_rows += f"""
            <tr>
              <td>{wh}</td>
              <td align="center">{doc_link}</td>
              <td align="center">{status_text}</td>
              <td align="center">{created_time}</td>
            </tr>
            """

        html_tables += f"""
        <h3 style="color: #1f2937; margin-top: 24px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px;">{region_name}</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width: 100%; border-color: #e5e7eb;">
          <tr style="background-color: #f9fafb;">
            <th align="left">Warehouse Branch</th>
            <th align="center">Stock Entry ID</th>
            <th align="center">Status</th>
            <th align="center">Logged Time</th>
          </tr>
          {table_rows}
        </table>
        """

    body = f"""
    <p>Hi Team,</p>
    <p>Here is the summary of <b>Fish Received at Branch</b> Stock Entries for yesterday, <b>{target_date}</b>:</p>
    {html_tables}
    <br>
    <p style="font-size: 11px; color: #6b7280;">This is an automated performance audit email from ERPNext.</p>
    """

    subject = f"[Fish Receipt Audit] Summary for {target_date}"

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=body,
        delayed=False,
        header=["Fish Intake Summary", "blue"],
    )