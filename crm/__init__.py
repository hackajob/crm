
__version__ = "1.52.9"
__title__ = "Frappe CRM"

def _patch_email():
		from crm.overrides import email_receive, email_account

_patch_email()
