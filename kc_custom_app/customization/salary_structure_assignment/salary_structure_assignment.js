function update_base(frm) {
    if (frm.doc.custom_exchange_rate && frm.doc.custom_foreign_base) {
        frm.set_value("base", frm.doc.custom_foreign_base * frm.doc.custom_exchange_rate);
    }
}

frappe.ui.form.on("Salary Structure Assignment", {
    custom_foreign_base: update_base,
    custom_exchange_rate: update_base
});