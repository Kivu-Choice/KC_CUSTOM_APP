import frappe

def _enabled():
    # reads from site_config.json -> "kc_custom_app_notifications_feature_enabled": 1
    return bool(frappe.conf.get("kc_custom_app_notifications_feature_enabled"))

def send_pending_po_notifications(batch_size=10):
    if not _enabled():
        return  # no-op on other sites

    try:
        pending_pos = frappe.get_all(
            "Purchase Order",
            filters={"workflow_state": ["not in", ["Draft", "Approved", "To Amend"]]},
            fields=["name", "workflow_state"]
        )
        total = len(pending_pos)
        for batch_start in range(0, total, batch_size):
            batch = pending_pos[batch_start:batch_start+batch_size]
            for po in batch:
                doc = frappe.get_doc("Purchase Order", po.name)
                # Get the workflow for Purchase Order
                workflow = frappe.get_doc("Workflow", {"name": "Purchase Order KC"})
                for state in workflow.states:
                    if state.state == doc.workflow_state:
                        role = state.allow_edit
                        # Get users with the role, but exclude those who are System Managers
                        users = frappe.get_all(
                            "Has Role",
                            filters={"role": role, "parenttype": "User"},
                            fields=["parent"]
                        )
                        filtered_users = []
                        for u in users:
                            # Exclude users who have the "System Manager" role
                            has_sys_mgr = frappe.db.exists(
                                "Has Role",
                                {"role": "System Manager", "parent": u.parent, "parenttype": "User"}
                            )
                            if not has_sys_mgr and frappe.db.get_value("User", u.parent, "enabled") == 1:
                                first_name = frappe.db.get_value("User", u.parent, "first_name")
                                filtered_users.append({"user": u.parent, "first_name": first_name})
                        for user_info in filtered_users:
                        # for user_info in users:
                            try:
                                url = frappe.utils.get_url_to_form(doc.doctype, doc.name)
                                pdf_attachment = frappe.attach_print(
                                    doctype=doc.doctype,
                                    name=doc.name,
                                    file_name=f"{doc.name}",
                                    print_format="Purchase Order",
                                    print_letterhead=True
                                )
                                frappe.sendmail(
                                    recipients=[user_info["user"]],
                                    cc=["huwizera@kivuchoice.com"],
                                    subject="Daily summary: Purchase Order(s) Pending Approval",
                                    message = f"Hello {user_info['first_name']},<br><br>Purchase Order <b><a href=\"{url}\">{doc.name}</a> for {doc.supplier}</b> is pending your approval.<br>",
                                    now=True,
                                    attachments=[pdf_attachment]
                                )
                            except Exception as e:
                                frappe.log_error(f"Email error for {user_info['user']}: {e}", "PO Notification Debug")
    except Exception as e:
        frappe.log_error(f"General error: {e}", "PO Notification Debug")
        
def send_po_approved_notification(doc, method):
    if not _enabled():
        return  # no-op on other sites

    try:
        #Get previous workflow state
        previous_doc = doc.get_doc_before_save()
        previous_state = previous_doc.workflow_state if previous_doc else None
        
        # Only send if transitioning to Approved
        if previous_state != "Approved" and doc.workflow_state == "Approved":
            #Fetch recipient emails
            owner_email = frappe.db.get_value("User", doc.owner, "email")
            supplier_email = frappe.db.get_value("Supplier", doc.supplier, "email_id")
            recipients = [e for e in [supplier_email, owner_email] if e]
            if not recipients:
                frappe.log_error(
                    title="PO Approved Email Notification",
                    message=f"No recipient email found for PO {doc.name} "
                            f"(supplier_email={supplier_email}, owner_email={owner_email})"
                )
                return

            # Compose and send email
            try:
                pdf_attachment = frappe.attach_print(
                    doctype=doc.doctype,
                    name=doc.name,
                    file_name=f"{doc.name}",
                    print_format="Purchase Order",
                    print_letterhead=True
                )
                frappe.sendmail(
                    recipients = recipients,
                    cc =["huwizera@kivuchoice.com"],
                    subject=f"Purchase Order {doc.name} from Kivu Choice Limited for {doc.supplier}",
                    message=(
                        f"Hello,<br><br>Please find attached Purchase Order <b>{doc.name} for {doc.grand_total} {doc.currency}</b>.<br>"
                        f"<br>The delivery due date, address and instructions are included in the Purchase Order.<br>"
                        f"<br>If you have any questions, please let us know. Thank you.<br>"
                        f"<br>Best Regards,<br>Kivu Choice Limited<br>"
                    ),
                    attachments=[pdf_attachment]
                )
            except Exception as e:
                    frappe.log_error(
                        title="PO Approved Email Notification",
                        message=f"Email sending failed for PO {doc.name}: {e}"
                    )
        else:
            return
          
    except Exception as e:
        # return
        frappe.log_error(
            title="PO Approved Email Notification",
            message=f"Fatal error in notification handler for PO {doc.name}: {e}"
        )