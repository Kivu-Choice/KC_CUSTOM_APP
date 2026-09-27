import frappe
from frappe.utils import get_url_to_form, getdate, nowdate

def _get_approver_by_job_level(employee_name: str, target_job_level: str) -> str | None:
    """
    Recursively traverses the 'reports_to' chain starting from the employee's direct manager
    until an active Employee matching the target_job_level is found.
    """
    current_employee = employee_name
    visited = set()

    while current_employee:
        if current_employee in visited:
            frappe.log_error(
                f"Circular reporting structure detected for employee {employee_name}",
                "Appraisal Traversal Error"
            )
            return None
        visited.add(current_employee)

        reports_to = frappe.db.get_value("Employee", current_employee, "reports_to")
        if not reports_to:
            return None

        manager_details = frappe.db.get_value(
            "Employee",
            reports_to,
            ["custom_job_level", "user_id", "status"],
            as_dict=True
        )

        if not manager_details or manager_details.status != "Active":
            current_employee = reports_to
            continue

        if manager_details.custom_job_level and manager_details.custom_job_level.strip().lower() == target_job_level.strip().lower():
            return manager_details.user_id or reports_to

        current_employee = reports_to

    return None

def _get_target_job_level_from_state(workflow_state: str) -> str | None:
    """Extracts required target job level from workflow state inside parentheses."""
    if not workflow_state or "Pending Approval" not in workflow_state:
        return None

    if "(" in workflow_state and ")" in workflow_state:
        return workflow_state.split("(")[1].split(")")[0].strip()

    return None


def _send_grouped_approval_emails(approver_grouped_items: dict):
    """
    Sends one consolidated email per approver containing a list of all their pending items.
    """
    # --- TESTING RECIPIENTS ---
    test_recipients = [
        "huwizera@kivuchoice.com",
        "cmukunzi@kivuchoice.com",
        "ashema@kivuchoice.com",
        "ikamanda@kivuchoice.com"
    ]

    for approver_user_id, items in approver_grouped_items.items():
        if not items:
            continue

        approver_name = (
            frappe.db.get_value("User", approver_user_id, "full_name")
            or frappe.db.get_value("Employee", approver_user_id, "employee_name")
            or approver_user_id
        )

        # Build combined table of pending appraisals
        items_rows_html = ""
        for item in items:
            doc_url = get_url_to_form("Appraisal", item["doc_name"])
            items_rows_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><b>{item['employee_name']}</b></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{item['department'] or 'N/A'}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{item['workflow_state']}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;"><a href="{doc_url}">Review Appraisal</a></td>
                </tr>
            """

        subject = f"[TESTING] Action Required: {len(items)} Pending Appraisal Approval(s) - {approver_name}"

        message = f"""
            <p>Dear <b>{approver_name}</b>,</p>
            <p>You have <b>{len(items)}</b> pending appraisal approval(s) requiring your review:</p>
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ddd;">Employee</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Department</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Status</th>
                        <th style="padding: 8px; border: 1px solid #ddd;">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {items_rows_html}
                </tbody>
            </table>
            <br>
            <p><b>Resolved Approver Account:</b> {approver_user_id}</p>
            <p><i>Automated digest test notification from Kivu Choice ERP.</i></p>
        """

        # --- PRODUCTION EMAIL LOGIC (DISABLED FOR TESTING) ---
        # approver_email = frappe.db.get_value("User", approver_user_id, "email") or approver_user_id
        # recipients = [approver_email] if (approver_email and "@" in approver_email) else []

        recipients = test_recipients

        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=message
            )


def process_appraisal_pending_notifications():
    """
    Checks active monthly cycles, processes unsubmitted appraisals,
    groups pending items by resolved approver, and sends consolidated emails.
    """
    today = getdate(nowdate())

    active_cycles = frappe.get_all(
        "Appraisal Cycle",
        filters={"docstatus": ["<", 2]},
        fields=["name", "start_date", "end_date"]
    )

    current_cycle_names = [
        cycle.name for cycle in active_cycles
        if cycle.start_date and cycle.end_date and
        getdate(cycle.start_date).month <= today.month <= getdate(cycle.end_date).month and
        getdate(cycle.start_date).year <= today.year <= getdate(cycle.end_date).year
    ]

    if not current_cycle_names:
        return

    open_appraisals = frappe.get_all(
        "Appraisal",
        filters={
            "kra_template": ["in", current_cycle_names],
            "docstatus": 0,
            "workflow_state": ["not in", ["Approved", "Rejected"]]
        },
        fields=["name", "employee", "employee_name", "department", "workflow_state", "custom_appraisal_approver"]
    )

    # Dictionary to aggregate pending items grouped by approver: { approver_user_id: [item1, item2, ...] }
    grouped_notifications = {}

    for appraisal_data in open_appraisals:
        doc = frappe.get_doc("Appraisal", appraisal_data.name)
        target_approver = None

        # 1. Draft state
        if doc.workflow_state == "Draft":
            if not doc.custom_appraisal_approver:
                direct_manager = frappe.db.get_value("Employee", doc.employee, "reports_to")
                doc.custom_appraisal_approver = frappe.db.get_value("Employee", direct_manager, "user_id") if direct_manager else None
                if doc.custom_appraisal_approver:
                    doc.save(ignore_permissions=True)

            target_approver = doc.custom_appraisal_approver

        # 2. Pending Approval states
        elif "Pending Approval" in (doc.workflow_state or ""):
            required_level = _get_target_job_level_from_state(doc.workflow_state)
            if required_level:
                approver = _get_approver_by_job_level(doc.employee, required_level)
                if approver and approver != doc.custom_appraisal_approver:
                    doc.custom_appraisal_approver = approver
                    doc.save(ignore_permissions=True)

                target_approver = approver or doc.custom_appraisal_approver

        # Group item under target approver
        if target_approver:
            grouped_notifications.setdefault(target_approver, []).append({
                "doc_name": doc.name,
                "employee_name": doc.employee_name,
                "department": doc.department,
                "workflow_state": doc.workflow_state
            })

    # Dispatch one email per approver with all grouped records
    if grouped_notifications:
        _send_grouped_approval_emails(grouped_notifications)