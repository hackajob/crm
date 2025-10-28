from frappe.core.doctype.communication.communication import Communication


class CustomCommunication(Communication):
	@staticmethod
	def default_list_data():
		columns = [
			{"label": "Sender", "type": "Data", "key": "sender", "width": "12rem"},
			{"label": "Receiver", "type": "Data", "key": "receiver", "width": "12rem"},
			{"label": "From", "type": "Data", "key": "phone_no", "width": "12rem"},
			{"label": "To", "type": "Data", "key": "recipients", "width": "12rem"},
			{"label": "Message", "type": "Text", "key": "content", "width": "1fr"},
			{"label": "Direction", "type": "Data", "key": "sent_or_received", "width": "8rem"},
			{"label": "When", "type": "Datetime", "key": "creation", "width": "10rem"},
		]

		rows = [
			"name",
			"creation",
			"sent_or_received",
			"sender",
			"receiver",
			"phone_no",
			"recipients",
			"content",
			"reference_doctype",
			"reference_name",
			"_liked_by",
		]

		return {"columns": columns, "rows": rows}