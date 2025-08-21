import frappe
from frappe.desk.doctype.notification_settings import notification_settings

_original_fn = notification_settings.is_email_notifications_enabled_for_type

def custom_is_email_notifications_enabled_for_type(user, notification_type):
    if notification_type == "Assignment":
        return False
    return _original_fn(user, notification_type)
