frappe.ui.form.on("Appraisal Goal", {
    score: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (!d.score) return;

        if (d.score < 1 || d.score > 5) {
            frappe.model.set_value(cdt, cdn, "score", 0);
            frappe.throw(__("Score should be between 1 to 5"));
        }

        // Floor to nearest 0.5 (e.g., 3.12 -> 3.0, 3.56 -> 3.5)
        let rounded_score = Math.floor(d.score * 2) / 2;

        if (d.score !== rounded_score) {
            frappe.model.set_value(cdt, cdn, "score", rounded_score);
            return;
        }

        let score_percentage = (rounded_score / 5) * 100;
        frappe.model.set_value(cdt, cdn, "score_percentage", score_percentage);
    },
});