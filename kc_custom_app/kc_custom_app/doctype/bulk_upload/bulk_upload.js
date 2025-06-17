// Copyright (c) 2025, Kivu Choice and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Upload', {
	get_draft_payments(frm) {
        frappe.call({
            method: 'get_pending_payments',
            doc: frm.doc,
            btn: $('.primary-action'),
            freeze: true,
            callback: (r) => {
                if (r.message) {
                    if(frm.doc.type=="BK Local Bank Transfer"){
                        processBKLocalDraftPayments(frm, r.message.draft_payments);
                    }else if(frm.doc.type=="I&M Local Bank Transfer"){
                        processIMLocalDraftPayments(frm, r.message.draft_payments, r.message.total_grand_total);
                    }                 
                } else {
                    console.log("No Draft Payments Match The Criteria.");
                }
            },
            error: (r) => {
                console.error("Error", r);
                // Handle the error here
            }
        })
    },
    
    download(frm) {
        frappe.call({
            method: 'download_report',
            doc: frm.doc,
            callback: function(r) {
                if(r.message) {
                    window.open(r.message);
                }
            }
        });
        
    }
});


function processBKLocalDraftPayments(frm, draftPymnts, grand_totals) {
    const childTableField = 'bk_local_bank_transfer';

    // Create a set of existing entries to check for duplicates
    const existingPymnts = new Set(frm.doc[childTableField].map(row => row.payment_reference)); // Assuming 'payment_reference' is a field in the child table
    draftPymnts.forEach(dp => {
         if (!existingPymnts.has(dp.name)) {
            let newRow = frm.add_child(childTableField);
            newRow.payment_reference = dp.name;
            newRow.bank_code = dp.bank_code;
            newRow.debit_account_number= dp.party_bank_account;
            newRow.debit_account_name = dp.bank_account;
            newRow.beneficiary_bank_name = dp.party; 
            newRow.beneficiary_account_name = dp.patry;
            newRow.beneficiary_account_number = dp.bank_account;
            // newRow.currency = dp.reference_no;
            newRow.amount = dp.paid_amount;

            existingPymnts.add(dp.name); // Add the new purchase order to the set of existing orders
        }
    });
    
    frm.doc.total_amount = grand_totals
    
    frm.refresh_field(childTableField); // Refresh the child table field to display the added rows
    frm.refresh_field('total_amount')
    frm.save()
}
function processIMLocalDraftPayments(frm, draftPymnts, grand_totals) {
    const childTableField = 'im_local_bank_transfer'; // Update this with the actual field name of your child table

    // Create a set of existing entries to check for duplicates
    const existingPymnts = new Set(frm.doc[childTableField].map(row => row.payment_reference)); // Assuming 'payment_reference' is a field in the child table
    draftPymnts.forEach(dp => {
         if (!existingPymnts.has(dp.name)) {
            let newRow = frm.add_child(childTableField);
            newRow.serial_number = dp.name; // Assuming 'payment_reference' is a field in the child table
            newRow.beneficiary_name = dp.party; // Assuming 'beneficiary_name' is a field in the child table
            newRow.bank_name = dp.bank_name;
            newRow.amount = dp.paid_amount; // Assuming 'amount' is a field in the child table
            existingPymnts.add(dp.name); // Add the new purchase order to the set of existing orders
        }
    });
    
    frm.doc.total_amount = grand_totals
    
    frm.refresh_field(childTableField); // Refresh the child table field to display the added rows
    frm.refresh_field('total_amount')
    frm.save()
}