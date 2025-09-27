import json

import frappe
from frappe import _
from frappe.utils import get_fullname


@frappe.whitelist()
def get_sms_messages(reference_doctype: str, reference_name: str):
	"""Return Communications of medium SMS for the given reference."""
	if not frappe.db.exists("DocType", "Communication"):
		return []

	fields = [
		"name",
		"sender",
		"sender_full_name",
		"recipients",
		"content",
		"sent_or_received",
		"communication_medium",
		"communication_date",
		"creation",
	]

	messages = frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"communication_type": "Communication",
			"communication_medium": "SMS",
		},
		fields=fields,
		order_by="creation asc",
	)
	return messages


@frappe.whitelist()
def send_sms_message(reference_doctype: str, reference_name: str, message: str, to: str):
	"""Send SMS via Frappe's SMS Settings and create a Communication of medium SMS."""
	# send actual SMS (best effort)
	try:
		from frappe.core.doctype.sms_settings.sms_settings import send_sms

		send_sms([to], message, success_msg=False)
	except Exception:
		# don't fail UI on SMS gateway issues; we still log the communication
		frappe.log_error(frappe.get_traceback(), "CRM SMS send failed")

	user = frappe.session.user
	# Create a Communication entry so that it appears in activity
	comm = frappe.get_doc(
		{
			"doctype": "Communication",
			"communication_type": "Communication",
			"communication_medium": "SMS",
			"content": message,
			"subject": _(f"SMS to {to}"),
			"sent_or_received": "Sent",
			"status": "Linked",
			"recipients": to,
			"sender": user,
			"sender_full_name": get_fullname(user),
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		}
	)
	comm.insert(ignore_permissions=True)

	# notify realtime channel so UI refreshes
	frappe.publish_realtime(
		"sms_message",
		{"reference_doctype": reference_doctype, "reference_name": reference_name},
	)
	return comm.name


@frappe.whitelist(allow_guest=True)
def receive_sms():

	from_number = str(frappe.form_dict.get("From"))
	to_number = str(frappe.form_dict.get("To"))
	body = str(frappe.form_dict.get("Body"))

	# Try to resolve the lead in as few DB hits as possible (fetch both name & lead_name)
	lead_row = frappe.db.get_value(
		"CRM Lead", {"mobile_no": from_number}, ["name", "lead_name"], as_dict=True
	)

	# Fallback: try stripping '+' if not found
	if not lead_row and from_number.startswith('+'):
		alt = from_number.lstrip('+')
		lead_row = frappe.db.get_value(
			"CRM Lead", {"mobile_no": alt}, ["name", "lead_name"], as_dict=True
		)

	lead_name = lead_row.name if lead_row else None
	lead_full_name = (
		lead_row.lead_name if (lead_row and lead_row.lead_name) else lead_name
	)

	# If still not found, we skip creating communication linked to lead
	ref_doctype = None
	ref_name = None
	if lead_name:
		ref_doctype = "CRM Lead"
		ref_name = lead_name

	# Save as Communication
	comm = frappe.get_doc({
		"doctype": "Communication",
		"communication_type": "Communication",
		"communication_medium": "SMS",
		"phone_no": from_number,
		"recipients": to_number,
		"subject": "SMS from " + from_number,
		"reference_doctype": ref_doctype,
		"reference_name": ref_name,
		"content": body,
		"status": "Linked" if ref_name else "Open",
		"sent_or_received": "Received",
		# Populate sender_full_name so UI can display originating lead's name
		"sender_full_name": lead_full_name,
	})
	comm.insert(ignore_permissions=True)
	frappe.db.commit()

	frappe.local.response["type"] = "binary"
	frappe.local.response["filename"] = "response.xml"
	frappe.local.response["filecontent"] = """<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>"""
	frappe.local.response["content_type"] = "text/xml"