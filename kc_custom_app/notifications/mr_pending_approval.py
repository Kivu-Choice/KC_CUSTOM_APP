import frappe

# def send_pending_mr_notifications(batch_size=10):
#     try:
#         pending_mrs = frappe.get_all(
#             "Material Request",
#             filters={"workflow_state": ["not in", ["Draft", "Approved", "To Amend"]]},
#             fields=["name", "workflow_state"]
#         )
#         total = len(pending_mrs)
#         for batch_start in range(0, total, batch_size):
#             batch = pending_mrs[batch_start:batch_start+batch_size]
#             for mr in batch:
#                 doc = frappe.get_doc("Material Request", mr.name)
#                 # Get the workflow for Material Request
#                 workflow = frappe.get_doc("Workflow", {"name": "Material Request KC"})
#                 for state in workflow.states:
#                     if state.state == doc.workflow_state:
#                         role = state.allow_edit
#                         # Get users with the role, but exclude those who are System Managers
#                         users = frappe.get_all(
#                             "Has Role",
#                             filters={"role": role, "parenttype": "User"},
#                             fields=["parent"]
#                         )
#                         filtered_users = []
#                         for u in users:
#                             # Exclude users who have the "System Manager" role
#                             has_sys_mgr = frappe.db.exists(
#                                 "Has Role",
#                                 {"role": "System Manager", "parent": u.parent, "parenttype": "User"}
#                             )
#                             if not has_sys_mgr and frappe.db.get_value("User", u.parent, "enabled") == 1:
#                                 first_name = frappe.db.get_value("User", u.parent, "first_name")
#                                 filtered_users.append({"user": u.parent, "first_name": first_name})
#                         for user_info in filtered_users:
#                         # for user_info in users:
#                             try:
#                                 url = frappe.utils.get_url_to_form(doc.doctype, doc.name)
#                                 frappe.sendmail(
#                                     recipients=[user_info["user"]],
#                                     cc=["huwizera@kivuchoice.com"],
#                                     subject="Daily summary: Material Request(s) Pending Approval",
#                                     message = f"Hello {user_info['first_name']},<br><br>Material Request <b><a href=\"{url}\">{doc.name}</a></b> is pending your approval.<br>",
#                                     now=True,
#                                 )
#                             except Exception as e:
#                                 frappe.log_error(f"Email error for {user_info['user']}: {e}", "MR Notification Debug")
#     except Exception as e:
#         frappe.log_error(f"General error: {e}", "MR Notification Debug")
        
def send_mr_approved_notification(doc, method):
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
                frappe.sendmail(
                    recipients=[owner_email],
                    cc=["huwizera@kivuchoice.com"],
                    subject=f"Material Request {doc.name} from Kivu Choice Limited",
                    message=(
                        f"Hello,<br><br>Please find attached a Material Request <b>{doc.name}</b>.<br>"
                        f"<br>If you have any questions, please let us know. Thank you</a>.<br>"
                        f"<br>Best Regards,<br>Kivu Choice Limited<br>"
                    )
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