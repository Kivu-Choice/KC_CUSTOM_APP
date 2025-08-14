import frappe

def _enabled():
    # reads from site_config.json -> "kc_custom_app_notifications_feature_enabled": 1
    return bool(frappe.conf.get("kc_custom_app_notifications_feature_enabled"))

def send_pending_mr_notifications(batch_size=10):
    if not _enabled():
        return  # no-op on other sites

    try:
        pending_mrs = frappe.get_all(
            "Material Request",
            filters={"workflow_state": ["not in", ["Draft", "Approved", "To Amend"]]},
            fields=["name", "workflow_state"]
        )

        if not pending_mrs:
            return

        total = len(pending_mrs)
        for batch_start in range(0, total, batch_size):
            batch = pending_mrs[batch_start:batch_start+batch_size]

            # Dictionary to store: {user_email: {"first_name": ..., "mrs": [(name, url), ...]}}
            user_mr_map = {}

            for mr in batch:
                doc = frappe.get_doc("Material Request", mr.name)
                # Get the workflow for Material Request
                workflow = frappe.get_doc("Workflow", {"name": "Material Request KC"})
                for state in workflow.states:
                    if state.state == doc.workflow_state:
                        role = state.allow_edit
                        # Get users with the role, but exclude those who are System Managers
                        users = frappe.get_all(
                            "Has Role",
                            filters={"role": role, "parenttype": "User"},
                            fields=["parent"]
                        )

                        for u in users:
                            # Exclude users who have the "System Manager" role
                            has_sys_mgr = frappe.db.exists(
                                "Has Role",
                                {"role": "System Manager", "parent": u.parent, "parenttype": "User"}
                            )
                            if not has_sys_mgr and frappe.db.get_value("User", u.parent, "enabled") == 1:
                                first_name = frappe.db.get_value("User", u.parent, "first_name")
                                url = frappe.utils.get_url_to_form(doc.doctype, doc.name)

                                if u.parent not in user_mr_map:
                                    user_mr_map[u.parent] = {"first_name": first_name, "mrs": []}
                                user_mr_map[u.parent]["mrs"].append((doc.name, url))

            # Send one email per user with all their MRs
            for user_email, info in user_mr_map.items():
                try:
                    mr_list_html = "".join(
                        [f'<li><a href="{url}">{name}</a></li>' for name, url in info["mrs"]]
                    )
                    message = (
                        f"Hello {info['first_name']},<br><br>"
                        "The following Material Request(s) are pending your approval:<br>"
                        f"<ul>{mr_list_html}</ul>"
                    )
                    frappe.sendmail(
                        recipients=[user_email],
                        cc=["huwizera@kivuchoice.com"],
                        subject="Daily summary: Material Request(s) Pending Approval",
                        message=message,
                        now=True,
                    )
                except Exception as e:
                    frappe.log_error(f"Email error for {user_email}: {e}", "MR Notification Debug")
    except Exception as e:
        frappe.log_error(f"General error: {e}", "MR Notification Debug")
        
def send_mr_approved_notification(doc, method):
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

            # Compose and send email
            try:
                url = frappe.utils.get_url_to_form(doc.doctype, doc.name)
                frappe.sendmail(
                    recipients=[owner_email],
                    cc=["huwizera@kivuchoice.com"],
                    subject=f"Material Request {doc.name} Approved",
                    message = f"Hello {user_info['first_name']},<br><br>Material Request <b><a href=\"{url}\">{doc.name}</a></b> has been approved.<br>"
                )
            except Exception as e:
                    frappe.log_error(
                        title="MR Approved Email Notification",
                        message=f"Email sending failed for MR {doc.name}: {e}"
                    )
        else:
            return
          
    except Exception as e:
        # return
        frappe.log_error(
            title="MR Approved Email Notification",
            message=f"Fatal error in notification handler for MR {doc.name}: {e}"
        )