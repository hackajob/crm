import frappe

LEAD_LINKED_DOCTYPES = {
	"Communication": "reference_name",
	"Comment": "reference_name",
	"File": "attached_to_name",
	"Dynamic Link": "link_name",
	"CRM Call Log": "reference_docname",
	"CRM Notification": "reference_name",
	"CRM Task": "reference_docname",
	"FCRM Note": "reference_docname",
}


@frappe.whitelist()
def delete_lead_and_links(name):
	# Telephony links a call through its `links` rows, which the Dynamic Link delete below would remove first.
	call_logs = frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "CRM Call Log", "link_doctype": "CRM Lead", "link_name": name},
		pluck="parent",
	)
	for call_log in set(call_logs):
		frappe.delete_doc("CRM Call Log", call_log, delete_permanently=True)

	# Permanently: a plain delete keeps a restorable copy of each document in Deleted Document.
	for doctype, fieldname in LEAD_LINKED_DOCTYPES.items():
		linked_docs = frappe.get_all(doctype, filters={fieldname: name})
		for doc in linked_docs:
			frappe.delete_doc(doctype, doc.name, delete_permanently=True)

	frappe.delete_doc("CRM Lead", name, delete_permanently=True)
