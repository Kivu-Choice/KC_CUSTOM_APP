// Copyright (c) 2026, Kivu Choice and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company Appraisal", {
  validate: function (frm) {
    if (frm.doc.score > 100) {
      frappe.msgprint("Score cannot be more than 100");
      frappe.validated = false;
    }
  }
});
