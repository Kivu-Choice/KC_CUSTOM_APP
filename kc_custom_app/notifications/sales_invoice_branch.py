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

def send_daily_sales_invoice_digest():
    """
    Daily digest summarizing Sales Invoices for TODAY grouped by set_warehouse.
    Expected execution at 7:00 PM via hooks.py cron schedule.
    """
    if not _enabled():
        return

    # Team Recipients
    recipients = [
        "gniyomuhoza@kivuchoice.com", 
        "eshema@kivuchoice.com", 
        "csugira@kivuchoice.com", 
        "ekayitare@kivuchoice.com", 
        "dbyiringiro@kivuchoice.com", 
        "dntaganda@kivuchoice.com", 
        "ckwisanga@kivuchoice.com", 
        "amuhire@kivuchoice.com", 
        "huwizera@kivuchoice.com",
        "dshema@kivuchoice.com", 
        "qniyigena@kivuchoice.com", 
        "ytumaini@kivuchoice.com", 
        "jngizwenayo@kivuchoice.com"
    ]
    if not recipients:
        return

    # Evaluates invoices logged today
    target_date = today()
    
    # Pull all matching Sales Invoices for today (including Cancelled)
    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "posting_date": target_date
        },
        fields=["name", "set_warehouse", "docstatus", "creation"],
        order_by="creation asc"
    )

    # Group multiple invoices by set_warehouse
    invoice_map = {}
    for inv in invoices:
        wh = inv.get("set_warehouse")
        if wh:
            if wh not in invoice_map:
                invoice_map[wh] = []
            invoice_map[wh].append(inv)

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
                # Loop through and report all invoices for this warehouse
                for idx, invoice in enumerate(wh_invoices):
                    status_text = get_status_badge(invoice["docstatus"])
                    doc_link = get_link_to_form("Sales Invoice", invoice["name"])
                    created_time = format_datetime(invoice["creation"], "HH:mm")
                    
                    rowspan_attr = f' rowspan="{len(wh_invoices)}"' if idx == 0 else ""
                    
                    table_rows += "<tr>"
                    if idx == 0:
                        table_rows += f"<td{rowspan_attr}>{wh}</td>"
                    table_rows += f"""
                      <td align="center">{doc_link}</td>
                      <td align="center">{status_text}</td>
                      <td align="center">{created_time}</td>
                    </tr>
                    """
            else:
                # Fallback for warehouses with no invoices today
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
    <p>Here is the daily audit summary of <b>Sales Invoice</b> records generated today, <b>{target_date}</b>, mapped by source warehouse:</p>
    {html_tables}
    <br>
    <p style="font-size: 11px; color: #9ca3af;">Automated Daily Digest | Kivu Choice ERPN Team</p>
    """

    subject = f"[Sales Invoice Audit] Summary for {target_date}"

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=body,
        delayed=False,
        header=["Sales Invoice Audit Summary", "blue"],
    )

def send_daily_sales_invoice_digest_night():
    """
    Wrapper function targeting the 9:30 PM cron execution.
    Bypasses Frappe's method uniqueness limitation in hooks.py scheduler setup.
    """
    send_daily_sales_invoice_digest()