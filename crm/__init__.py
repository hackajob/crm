
__version__ = "1.52.9"
__title__ = "Frappe CRM"

def _patch_email():
		from crm.overrides import email_receive, email_account

def _patch_notification_settings():
		from crm.overrides.notification_settings import (
				custom_is_email_notifications_enabled_for_type,
		)
		from frappe.desk.doctype.notification_settings import notification_settings

		notification_settings.is_email_notifications_enabled_for_type = (
				custom_is_email_notifications_enabled_for_type
		)

_patch_email()
_patch_notification_settings()