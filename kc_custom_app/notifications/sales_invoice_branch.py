import frappe
from frappe.utils import today, format_datetime, get_link_to_form

FEATURE_FLAG = "kc_custom_app_notifications_feature_enabled"

REGIONS = {
    "Kigali East": ["Kimironko - KC", "Remera-Giporoso - KC", "Kabuga - KC", "Kanombe - KC"],
    "Kigali Central": ["Kiyovu - KC", "Gikondo - KC", "Gatenga - KC", "Ziniya - KC"],
    "Kigali West": ["Batsinda - KC", "Gisozi - KC", "Nyabugogo - KC", "Nyamirambo - KC"],
    "Kivu Belt": ["Rusizi 1 - KC", "Kamembe Town - KC", "Rwesero - KC", "Tyazo - KC", "Mobile Branch - KC", "Rubavu Town - KC"],
    "Traders": ["Goma Traders - KC", "Bukavu Traders - KC"],
    "Projects": ["HORECA - KC", "D2C - KC"]
}

def _enabled() -> bool:
    return bool(frappe.conf.get(FEATURE_FLAG))

def send_daily_sales_invoice_digest(run_type="Evening"):
    if not _enabled():
        return

    # Atomic execution lock (prevents duplicate runs across multiple background workers)
    lock_key = f"lock:sales_invoice_digest:{today()}:{run_type}"
    if not frappe.cache().add(lock_key, "locked", expires_in_sec=300):
        return

    # Force MariaDB to discard stale snapshot isolation and read committed data
    frappe.db.rollback()

    recipients = [
        "gniyomuhoza@kivuchoice.com", 
        "eshema@kivuchoice.com", 
        "csugira@kivuchoice.com", 
        "ekayitare@kivuchoice.com", 
        "fbyiringiro@kivuchoice.com", 
        "dntaganda@kivuchoice.com", 
        "ckwisanga@kivuchoice.com", 
        "huwizera@kivuchoice.com",
        "dshema@kivuchoice.com", 
        "qniyigena@kivuchoice.com", 
        "ytumaini@kivuchoice.com", 
        "jngizwenayo@kivuchoice.com",
        "jkagabo@kivuchoice.com"
    ]
    if not recipients:
        return

    target_date = today()

    invoices = frappe.db.sql("""
        SELECT name, set_warehouse, docstatus, creation
        FROM `tabSales Invoice`
        WHERE posting_date = %s
        ORDER BY creation ASC
    """, (target_date,), as_dict=True)

    invoice_map = {}
    for inv in invoices:
        wh = inv.get("set_warehouse")
        if wh:
            invoice_map.setdefault(wh, []).append(inv)

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
            wh_invoices = invoice_map.get(wh, [])
            
            if wh_invoices:
                for idx, invoice in enumerate(wh_invoices):
                    status_text = get_status_badge(invoice["docstatus"])
                    doc_link = get_link_to_form("Sales Invoice", invoice["name"])
                    created_time = format_datetime(invoice["creation"], "HH:mm")
                    
                    rowspan_attr = f' rowspan="{len(wh_invoices)}"' if idx == 0 else ""
                    
                    table_rows += f"""
                    <tr>
                      {f'<td{rowspan_attr}>{wh}</td>' if idx == 0 else ''}
                      <td align="center">{doc_link}</td>
                      <td align="center">{status_text}</td>
                      <td align="center">{created_time}</td>
                    </tr>
                    """
            else:
                status_text = '<span style="color: #ef4444; font-style: italic;">No Invoices Found</span>'
                table_rows += f"""
                <tr>
                  <td>{wh}</td>
                  <td align="center">-</td>
                  <td align="center">{status_text}</td>
                  <td align="center">-</td>
                </tr>
                """

        html_tables += f"""
        <h3 style="color: #1f2937; margin-top: 24px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px;">{region_name}</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width: 100%; border-color: #e5e7eb;">
          <tr style="background-color: #f9fafb;">
            <th align="left">Warehouse</th>
            <th align="center">Sales Invoice ID</th>
            <th align="center">Status</th>
            <th align="center">Logged Time</th>
          </tr>
          {table_rows}
        </table>
        """

    body = f"""
    <p>Hi Team,</p>
    <p>Here is the daily ({run_type}) audit summary of <b>Sales Invoice</b> records generated today, <b>{target_date}</b>, mapped by source warehouse:</p>
    {html_tables}
    <br>
    <p style="font-size: 11px; color: #9ca3af;">Automated Daily Digest | Kivu Choice ERPN Team</p>
    """

    subject = f"[Sales Invoice Audit - {run_type}] Summary for {target_date}"

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=body,
        delayed=False,
        header=[f"Sales Invoice Audit Summary ({run_type})", "blue"],
    )

def send_daily_sales_invoice_digest_night():
    send_daily_sales_invoice_digest(run_type="Night")