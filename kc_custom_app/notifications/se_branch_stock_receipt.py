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

def send_daily_fish_received_digest(execution_label="Evening"):
    if not _enabled():
        return

    # Atomic execution lock (prevents duplicate runs across multiple background workers)
    lock_key = f"lock:fish_received_digest:{today()}:{execution_label}"
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
    all_target_entry_types = list(set([item for sublist in ENTRY_TYPES.values() for item in sublist]))

    entries = frappe.db.sql("""
        SELECT name, to_warehouse, stock_entry_type, docstatus, creation
        FROM `tabStock Entry`
        WHERE posting_date = %s
          AND stock_entry_type IN %s
        ORDER BY creation ASC
    """, (target_date, tuple(all_target_entry_types)), as_dict=True)

    entry_map = {}
    for e in entries:
        wh = e.get("to_warehouse")
        if wh:
            entry_map.setdefault(wh, []).append(e)

    def get_status_badge(docstatus):
        if docstatus == 0:
            return '<span style="color: #d97706; font-weight: bold;">Draft</span>'
        elif docstatus == 1:
            return '<span style="color: #16a34a; font-weight: bold;">Submitted</span>'
        return '<span style="color: #dc2626; font-weight: bold;">Cancelled</span>'

    html_tables = ""
    for region_name, warehouses in REGIONS.items():
        allowed_types = ENTRY_TYPES.get(region_name, [])
        table_rows = ""
        
        for wh in warehouses:
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
                    
                    table_rows += f"""
                    <tr>
                      {f'<td{rowspan_attr}>{wh}</td>' if idx == 0 else ''}
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
    <p>Here is the daily audit summary ({execution_label}) of <b>Fish Operations & Transfers</b> for today, <b>{target_date}</b>:</p>
    {html_tables}
    <br>
    <p style="font-size: 11px; color: #9ca3af;">Automated Daily Digest | Kivu Choice ERPNext Team</p>
    """

    subject = f"[{execution_label} Audit] Daily Fish Movement Summary for {target_date}"

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=body,
        delayed=False,
        header=["Daily Fish Movement Summary", "blue"],
    )

def send_daily_fish_received_digest_night():
    send_daily_fish_received_digest(execution_label="Night")