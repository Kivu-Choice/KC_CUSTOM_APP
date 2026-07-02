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

# Maps each Region group to its respective Stock Entry Type rule
ENTRY_TYPES = {
    "Kigali East": ["Fish Received at Branch"],
    "Kigali Central": ["Fish Received at Branch"],
    "Kigali West": ["Fish Received at Branch"],
    "Kivu Belt": ["Fish Received at Branch"],
    "Traders": ["Fish Transfer to Traders"],
    "Projects": ["Fish Transfer to Projects"]
}

def _enabled() -> bool:
    return bool(frappe.conf.get(FEATURE_FLAG))

def send_daily_fish_received_digest():
    """
    Daily digest summarizing Fish Movement (Branch Receipts, Trader Transfers, Project Transfers) for TODAY.
    Expected execution at 7:00 PM via hooks.py cron schedule.
    """
    if not _enabled():
        return

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

    target_date = today()
    
    # Extract unique entry types required for the query
    all_target_entry_types = list(set([item for sublist in ENTRY_TYPES.values() for item in sublist]))

    # Fetch entries for today matching any of our custom entry types
    entries = frappe.get_all(
        "Stock Entry",
        filters={
            "stock_entry_type": ["in", all_target_entry_types],
            "posting_date": target_date
        },
        fields=["name", "to_warehouse", "stock_entry_type", "docstatus", "creation"],
        order_by="creation asc"
    )

    # Group entries by warehouse
    entry_map = {}
    for e in entries:
        wh = e.get("to_warehouse")
        if wh:
            if wh not in entry_map:
                entry_map[wh] = []
            entry_map[wh].append(e)

    def get_status_badge(docstatus):
        if docstatus == 0:
            return '<span style="color: #d97706; font-weight: bold;">Draft</span>'
        elif docstatus == 1:
            return '<span style="color: #16a34a; font-weight: bold;">Submitted</span>'
        return '<span style="color: #dc2626; font-weight: bold;">Cancelled</span>'

    html_tables = ""
    for region_name, warehouses in REGIONS.items():
        # Identify acceptable entry types for this specific block
        allowed_types = ENTRY_TYPES.get(region_name, [])
        table_rows = ""
        
        for wh in warehouses:
            # Filter entries matching this warehouse AND matching the correct regional entry type rule
            wh_entries = [
                e for e in entry_map.get(wh, []) 
                if e["stock_entry_type"] in allowed_types
            ]
            
            if wh_entries:
                for idx, entry in enumerate(wh_entries):
                    status_text = get_status_badge(entry["docstatus"])
                    doc_link = get_link_to_form("Stock Entry", entry["name"])
                    created_time = format_datetime(entry["creation"], "HH:mm")
                    
                    rowspan_attr = f' rowspan="{len(wh_entries)}"' if idx == 0 else ""
                    
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
                status_text = '<span style="color: #ef4444; font-style: italic;">No Entry Found</span>'
                table_rows += f"""
                <tr>
                  <td>{wh}</td>
                  <td align="center">-</td>
                  <td align="center">{status_text}</td>
                  <td align="center">-</td>
                </tr>
                """

        # Generate region subheader with entry type context info
        type_hint = ", ".join(allowed_types)
        html_tables += f"""
        <h3 style="color: #1f2937; margin-top: 24px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; margin-bottom: 8px;">
            {region_name} <span style="font-size: 12px; font-weight: normal; color: #6b7280;">({type_hint})</span>
        </h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width: 100%; border-color: #e5e7eb;">
          <tr style="background-color: #f9fafb;">
            <th align="left">Warehouse</th>
            <th align="center">Stock Entry ID</th>
            <th align="center">Status</th>
            <th align="center">Logged Time</th>
          </tr>
          {table_rows}
        </table>
        """

    body = f"""
    <p>Hi Team,</p>
    <p>Here is the daily audit summary of <b>Fish Operations & Transfers</b> for today, <b>{target_date}</b>:</p>
    {html_tables}
    <br>
    <p style="font-size: 11px; color: #9ca3af;">Automated Daily Digest | Kivu Choice ERPN team</p>
    """

    subject = f"[Daily Fish Movement Audit] Summary for {target_date}"

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=body,
        delayed=False,
        header=["Daily Fish Movement Summary", "blue"],
    )

def send_daily_fish_received_digest_night():
    """
    Wrapper function targeting the 9:30 PM cron execution. 
    Bypasses Frappe's method uniqueness limitation in hooks.py scheduler setup.
    """
    send_daily_fish_received_digest()