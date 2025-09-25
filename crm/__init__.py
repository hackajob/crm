
__version__ = "1.52.11"
__title__ = "Frappe CRM"

def _rebind_imported_symbol(attr_name: str, original_fn, replacement_fn, module_prefixes=("frappe.", "erpnext.", "crm.")):
	"""Best-effort: rebind stale imported-by-name references across loaded modules.

	- attr_name: attribute to look for (e.g., "is_email_notifications_enabled_for_type").
	- original_fn: the original function object to match by identity.
	- replacement_fn: the new function to assign.
	- module_prefixes: only touch modules whose name starts with any of these prefixes.
	"""
	if not original_fn or not replacement_fn:
		return
	try:
		import sys
		for mod_name, mod in list(sys.modules.items()):
			if not mod or not isinstance(mod_name, str):
				continue
			if not any(mod_name.startswith(p) for p in module_prefixes):
				continue
			try:
				if hasattr(mod, attr_name) and getattr(mod, attr_name) is original_fn:
					setattr(mod, attr_name, replacement_fn)
			except Exception:
				# Ignore modules we cannot introspect or assign
				pass
	except Exception:
		# Best-effort safety net shouldn't break startup
		pass

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

		# Rebind any stale imported-by-name references globally
		from crm.overrides import notification_settings as _crm_override
		_original = getattr(_crm_override, "_original_fn", None)
		_rebind_imported_symbol(
			"is_email_notifications_enabled_for_type",
			_original,
			custom_is_email_notifications_enabled_for_type,
		)

_patch_email()
_patch_notification_settings()