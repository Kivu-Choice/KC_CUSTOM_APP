frappe.ui.form.on("Appraisal Goal", {
    score: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (!d.score) return;

        if (d.score < 1 || d.score > 5) {
            frappe.model.set_value(cdt, cdn, "score", 0);
            frappe.throw(__("Score should be between 1 to 5"));
        }

        let rounded_score = Math.round(d.score);
        if (d.score !== rounded_score) {
            frappe.model.set_value(cdt, cdn, "score", rounded_score);
        }
    },
});