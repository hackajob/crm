import frappe


@frappe.whitelist()
def delete_lead_and_links(name):
	linked_doctypes = {
		'Communication': 'reference_name',
		'Comment': 'reference_name',
		'File': 'attached_to_name',
		'Dynamic Link': 'link_name',
		'CRM Call Log': 'reference_docname',
		'CRM Notification': 'reference_name',
		'CRM Task': 'reference_docname',
		'FCRM Note': 'reference_docname',
	}
	for doctype, fieldname in linked_doctypes.items():
		linked_docs = frappe.get_all(doctype, filters={fieldname: name})
		for doc in linked_docs:
			frappe.delete_doc(doctype, doc.name)

	frappe.delete_doc('CRM Lead', name)
	frappe.db.commit()

@frappe.whitelist()
def can_delete_lead(name: str) -> bool:
	"""Return True if current user has Delete permission on the given Lead."""
	try:
		doc = frappe.get_doc('CRM Lead', name)
	except frappe.DoesNotExistError:
		return False
	return bool(frappe.has_permission('CRM Lead', doc=doc, ptype='delete'))
