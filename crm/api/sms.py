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
