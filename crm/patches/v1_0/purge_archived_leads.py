import json

import frappe

from crm.api.lead import LEAD_LINKED_DOCTYPES


def execute():
	archived_leads = set(
		frappe.get_all("Deleted Document", filters={"deleted_doctype": "CRM Lead"}, pluck="deleted_name")
	)
	if not archived_leads:
		return

	archives = set()
	purged_documents = set()
	for doctype, fieldname in LEAD_LINKED_DOCTYPES.items():
		for row in frappe.get_all(
			"Deleted Document", filters={"deleted_doctype": doctype}, fields=["name", "deleted_name", "data"]
		):
			data = json.loads(row.data)
			if data.get(fieldname) in archived_leads or _links_to(data, archived_leads):
				archives.add(row.name)
				purged_documents.add((doctype, row.deleted_name))

	# Deleting a communication or a note archived its attachments too, keyed to that document.
	for row in frappe.get_all(
		"Deleted Document", filters={"deleted_doctype": "File"}, fields=["name", "data"]
	):
		data = json.loads(row.data)
		if (data.get("attached_to_doctype"), data.get("attached_to_name")) in purged_documents:
			archives.add(row.name)

	if archives:
		frappe.db.delete("Deleted Document", {"name": ["in", list(archives)]})
	frappe.db.delete("Deleted Document", {"deleted_doctype": "CRM Lead"})


def _links_to(data, archived_leads):
	return any(
		link.get("link_doctype") == "CRM Lead" and link.get("link_name") in archived_leads
		for link in data.get("links") or []
	)
