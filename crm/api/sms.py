import json

import frappe
from frappe import _
from frappe.utils import get_fullname
from crm.api.doc import get_assigned_users
from crm.integrations.twilio.twilio_handler import get_twilio_number_owners
from frappe.core.doctype.sms_settings.sms_settings import send_sms


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
	try:
		send_sms([to], message, success_msg=False)
	except Exception:
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
		"sender_full_name": lead_full_name,
	})
	comm.insert(ignore_permissions=True)

	# notify UI to refresh any open SMS views
	if ref_doctype and ref_name:
		frappe.publish_realtime(
			"sms_message",
			{"reference_doctype": ref_doctype, "reference_name": ref_name},
		)

	recipients = []
	try:
		owners = get_twilio_number_owners(to_number) if to_number else {}
		recipients = list(owners.keys()) if owners else []
	except Exception:
		# fallback to assignees on the referenced doc
		recipients = []
	if not recipients and ref_doctype and ref_name:
		recipients = get_assigned_users(ref_doctype, ref_name) or []

	if recipients:
		owner = "Administrator"
		try:
			owner_doc = frappe.get_doc("User", {
				"full_name": "hackajob Bot"
			})
			if owner_doc:
				owner = owner_doc.name
		except Exception:
			pass
		assignee = recipients[0]
		_prev_user = frappe.session.user
		try:
			frappe.set_user(owner)
			title_name = lead_full_name or from_number
			task_title = _(f"New SMS from {title_name}")
			description = _(f"Message: {body}\nFrom: {from_number}\nTo: {to_number}")
			values = frappe._dict(
				doctype="CRM Task",
				assigned_to=assignee,
				title=task_title,
				description=description,
				priority="Medium",
				start_date=frappe.utils.now_datetime(),
			)
			if ref_doctype and ref_name:
				values.update({
					"reference_doctype": ref_doctype,
					"reference_docname": ref_name,
				})
			frappe.get_doc(values).insert(ignore_permissions=True)
		finally:
			# restore previous session user
			try:
				frappe.set_user(_prev_user)
			except Exception:
				pass

	frappe.db.commit()

	frappe.local.response["type"] = "binary"
	frappe.local.response["filename"] = "response.xml"
	frappe.local.response["filecontent"] = """<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>"""
	frappe.local.response["content_type"] = "text/xml"


@frappe.whitelist()
def get_agent_numbers(users: str | list | None = None):
	"""Return mapping of user -> telephony number for given users.

	Picks in order: CRM Telephony Agent.mobile_no (computed primary), then twilio_number,
	then exotel_number. Returns empty string if none found. Accepts a JSON string or list.
	"""
	if not users:
		return {}
	if isinstance(users, str):
		try:
			users = json.loads(users)
		except Exception:
			users = [users]
	if not isinstance(users, (list, tuple)):
		users = [users]

	res = {}
	try:
		records = frappe.get_all(
			"CRM Telephony Agent",
			filters={"user": ["in", list(set(users))]},
			fields=["user", "mobile_no", "twilio_number", "exotel_number"],
		)
		for r in records:
			number = r.mobile_no or r.twilio_number or r.exotel_number or ""
			res[r.user] = number
	except Exception:
		# fail quietly, return empty mappings
		pass
	return res


@frappe.whitelist()
def get_agents_by_numbers(numbers: str | list | None = None):
	"""Return mapping of twilio_number -> { user, full_name, user_image } for given numbers.

	Accepts a JSON string or list of numbers. Matches CRMTelephonyAgent.twilio_number only (as requested).
	"""
	if not numbers:
		return {}
	if isinstance(numbers, str):
		try:
			numbers = json.loads(numbers)
		except Exception:
			numbers = [numbers]
	if not isinstance(numbers, (list, tuple)):
		numbers = [numbers]

	# Normalize to strings and unique
	numbers = [str(n) for n in numbers if n]
	if not numbers:
		return {}

	res = {}
	try:
		agents = frappe.get_all(
			"CRM Telephony Agent",
			filters={"twilio_number": ["in", list(set(numbers))]},
			fields=["user", "twilio_number"],
		)
		for a in agents:
			full_name, image = frappe.db.get_value("User", a.user, ["full_name", "user_image"]) or (a.user, None)
			res[a.twilio_number] = {"user": a.user, "full_name": full_name or a.user, "user_image": image}
	except Exception:
		pass
	return res