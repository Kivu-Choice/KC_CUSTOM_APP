frappe.ui.form.on('Purchase Receipt', {
    on_submit: function(frm) {
        frappe.call({
            method: "kc_custom_app.custom_scripts.server_scripts.purchase_receipt.create_landed_cost_voucher",
            args: {
                message:{
                    r_name: frm.doc.name
                }
            },
            callback: function(response) {
                if (response.message) {
                    console.log(response.message)
                    frappe.msgprint(`Landed Cost Voucher created: ${response.message}`);
                } else {
                    frappe.msgprint('Failed to create Landed Cost Voucher.');
                }
            }
        });
    }
});
