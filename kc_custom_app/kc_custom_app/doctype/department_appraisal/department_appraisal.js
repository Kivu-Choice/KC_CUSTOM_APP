// Copyright (c) 2026, Kivu Choice and contributors
// For license information, please see license.txt

frappe.ui.form.on("Department Appraisal", {
    validate: function (frm) {
        if (frm.doc.docstatus === 0 && frm.doc.goals.length > 0) {
            let total_score = 0;

            frm.doc.goals.forEach((element) => {
                total_score += element.score_earned;
            });
            frm.doc.appraisal_multiplier.forEach((element) => {
                total_score *= element.score;
            });

            frm.doc.total_goal_score = total_score;
            cur_frm.refresh_field("total_goal_score");
            frm.doc.total_goal_score_percentage = (frm.doc.total_goal_score / 5) * 100;
            cur_frm.refresh_field("total_goal_score_percentage");
        }
    },
    refresh: function (frm) {
        cur_frm.set_query("appraisal_template", function () {
            return {
                filters: {
                    custom_department_template: 1,
                },
            };
        });
        cur_frm.set_query("multiplier_template", function () {
            return {
                filters: {
                    custom_multiplier_template: 1,
                },
            };
        });
    },

    appraisal_template(frm) {
        if (frm.doc.appraisal_template) {
            frm.call("set_kras", {"parenttype": "appraisal_template"}, () => {
                frm.refresh_field("goals");
            });
        }
    },
    multiplier_template(frm) {
        if (frm.doc.multiplier_template) {
            frm.call("set_kras", {"parenttype": "multiplier_template"}, () => {
                frm.refresh_field("appraisal_multiplier");
            });
        }
    },
     //Get approvers from department
     department: function(frm) {
        if (frm.doc.department) {
            frappe.call({
                method: "kc_custom_app.kc_custom_app.doctype.department_appraisal.department_appraisal.get_approvers",
                args: {
                    department: frm.doc.department
                },
                callback: function(response) {
                    if (response.message && response.message.length > 0) {

                        // Clear existing child rows
                        frm.clear_table('appraisal_approver');

                        // Loop through each approver and add to child table
                        response.message.forEach(function(approver) {
                            var new_approver = frm.add_child('appraisal_approver');
                            new_approver.approver = approver;
                        });

                        // Refresh the table to reflect the changes
                        frm.refresh_field('appraisal_approver');
                    }
                }
            });
        }
    },
 
});

frappe.ui.form.on("Appraisal Goal", {
    score_percentage: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let score = (row.score_percentage * 5) / 100;
        let score_earned = score * (row.per_weightage / 100);
        frappe.model.set_value(cdt, cdn, "score", score);
        frappe.model.set_value(cdt, cdn, "score_earned", score_earned);
    },
    score: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        let score_percentage = (row.score / 5) * 100;
        let score_earned = row.score * (row.per_weightage / 100);
        frappe.model.set_value(cdt, cdn, "score_earned", score_earned);
        frappe.model.set_value(cdt, cdn, "score_percentage", score_percentage);
    },
});
