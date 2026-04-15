frappe.ui.form.on("Department Appraisal", {
    refresh: function (frm) {
        // 1. Render scoring references
        render_goal_template(frm);

        // 2. Add Preview Button
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Preview'), function() {
                show_appraisal_preview(frm);
            }, __("Actions"));
        }
    },

    department: function (frm) {
        render_goal_template(frm);
    },

    multiplier_template: function(frm) {
        // 3. Set default multiplier scores
        frappe.after_ajax(() => {
            frm.fields_dict['appraisal_multiplier'].grid.refresh();
            setTimeout(() => {
                frm.doc.appraisal_multiplier.forEach(row => {
                    if (!row.score) row.score = "1";
                });
                frm.refresh_field('appraisal_multiplier');
            }, 10);
        });
    }
});

// Helper Function for Script 1
function render_goal_template(frm) {
    if (!frm.doc.department) {
        if(frm.fields_dict.custom_scoring_references) {
            frm.fields_dict.custom_scoring_references.$wrapper.html("<p><i>Please select a department.</i></p>");
        }
        return;
    }
    frappe.call({
        method: "kc_custom_app.customization.department_appraisal.department_appraisal.get_rendered_scoring_references",
        args: { department: frm.doc.department, doc_name: frm.doc.name },
        callback: (r) => {
            frm.fields_dict.custom_scoring_references.$wrapper.html(r.message || "<p><i>Unable to load template.</i></p>");
        }
    });
}

// Helper Function for Script 2
function show_appraisal_preview(frm) {
    frappe.call({
        method: "frappe.client.get",
        args: { doctype: "Department Appraisal", name: frm.doc.name },
        callback: function(r) {
            if (!r.message) return;
            let doc = r.message;
            let d = new frappe.ui.Dialog({
                title: __("Appraisal Preview"),
                size: "large",
                fields: [{ fieldname: "html_preview", fieldtype: "HTML" }]
            });

            let html = `<div style="padding: 10px; font-size: 14px;"><h3>${doc.name}</h3><p><b>Department:</b> ${doc.department || ''}</p><hr><table class="table table-bordered" style="width:100%;"><thead><tr><th>Goal</th><th>Weight</th><th>Score</th><th>Remarks</th></tr></thead><tbody>`;
            (doc.goals || []).forEach(goal => {
                html += `<tr><td>${goal.kra || goal.goal || ''}</td><td>${goal.per_weightage || goal.weight || ''}</td><td>${goal.score || ''}</td><td>${goal.custom_remarks || goal.comment || ''}</td></tr>`;
            });
            html += `</tbody></table><hr><h4>Summary Scores</h4><p><b>Total Score:</b> ${doc.total_goal_score || ''}</p></div>`;

            d.get_field("html_preview").$wrapper.html(html);
            d.show();
        }
    });
}