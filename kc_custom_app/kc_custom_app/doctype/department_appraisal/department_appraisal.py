# Copyright (c) 2026, Kivu Choice and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DepartmentAppraisal(Document):
    def validate(self):
        appraisals = frappe.db.get_all('Department Appraisal', 
            filters = { 
                'company' : self.company, 
                'department' : self.department, 
                'appraisal_cycle' : self.appraisal_cycle, 
                'docstatus' : ['<', 2],
                'name': ['!=', self.name]
            }, 
            pluck = 'name'
        )
        if appraisals:
            frappe.throw(f"Appraisal {appraisals[0]} within the same appraisal cycle already exists.")


    @frappe.whitelist()
    def set_kras(self, parenttype = "appraisal_template"):
        if not self.appraisal_cycle:
            return

        value = self.appraisal_template 
        child_table = "goals"
        kra_key = "kra"
        score = "per_weightage"
        if parenttype != "appraisal_template":
            value = self.multiplier_template
            child_table = "appraisal_multiplier"
            kra_key = "template"
            score = "score"

        self.set(child_table, [])

        template = frappe.get_doc("Appraisal Template", value)

        for entry in template.goals:

            self.append(
                child_table,
                {
                    kra_key: entry.key_result_area,
                    score: entry.per_weightage if parenttype == "appraisal_template" else 0 ,
                }
            )

        return self
    def before_save(self):
        approvers=[]
        for approver in self.appraisal_approver:
            approvers.append(approver.approver)
        approvers.append(self.owner)
        if frappe.session.user not in approvers:
            frappe.throw("You are not allowed to save/submit this appraisal")
        
    def before_submit(self):
        for approver in self.appraisal_approver:
            if not approver.custom_approve:
                frappe.throw("Please send to the next approver.")
        if frappe.session.user!=get_last_approver(self.appraisal_approver):
            frappe.throw(f"This appraisal can only be submitted by <strong>{get_last_approver(self.appraisal_approver)}<span style='color:red'>!!</span></strong>")

   #Still testing with other methods ---after_save not working
    def on_update(self):	
        send_emails_to_approver(self.name)
        if frappe.session.user==get_last_approver(self.appraisal_approver):
            if self.docstatus==0:
                frappe.msgprint("You can now submit the test")
            else:
                frappe.msgprint("Thank you for submitting department appraisal💐")
     

@frappe.whitelist(allow_guest=True)
def get_approvers():
    department_name=frappe.form_dict.get("department")

    user_list=[]
    doc=frappe.get_doc("Department", department_name)
    approvers=doc.custom_appraisal_approvers
    if approvers:
        for approver in approvers:
            user=approver.get("approver")
            user_list.append(user)
    frappe.response['message']=user_list
    return user_list

def send_emails_to_approver(name):
    doc=frappe.get_doc('Department Appraisal',name)
    approvers=doc.appraisal_approver
    current_approver=get_approver_email(approvers)
    if not doc.email_template:
        doc.email_template="Department Appraisal"
    
    send_mail(current_approver, doc.email_template, doc)
        
def get_approver_email(approvers):
    for approver in approvers:
        if not approver.custom_approve:
            return approver.approver
    return None  
    
def get_last_approver(approvers):
    if approvers:
        last_approver = approvers[-1].approver
        return last_approver
    return None

def send_mail(email, template, appraisal_doc):
    if email is None:
        return
    email_template = frappe.get_doc("Email Template", template)
    context = {
        "name": appraisal_doc.name,
        "department": appraisal_doc.department,
        "total_goal_score":appraisal_doc.total_goal_score,
        "total_goal_score_percentage":appraisal_doc.total_goal_score_percentage,
        
    }
 
    try:
        frappe.sendmail(
            recipients=[email],
            subject="Appraisal Approval Request",
            message=frappe.render_template(email_template.response_html,context, is_path=False),
            
        )
        frappe.msgprint(f"Email sent successfully to {email}")
    except Exception as e:
        frappe.throw(f"Error sending email: {e}")
 
