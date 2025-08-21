import frappe
from frappe import _
from frappe.email.doctype.email_account.email_account import EmailAccount, InboundMail

# Custom get_inbound_mails method(frappe.email.doctype.email_account.email_account.EmailAccount.get_inbound_mails)
def custom_get_inbound_mails(self) -> list[InboundMail]:
    """Retrieve and return inbound mails with fixed folder handling."""
    mails = []

    def process_mail(messages, append_to=None):
        for index, message in enumerate(messages.get("latest_messages", [])):
            uid = messages["uid_list"][index] if messages.get("uid_list") else None
            seen_status = messages.get("seen_status", {}).get(uid)
            if self.email_sync_option != "UNSEEN" or seen_status != "SEEN":
                mails.append(
                    InboundMail(
                        message,
                        self,
                        frappe.safe_decode(uid),
                        seen_status,
                        append_to,
                    )
                )

    if not self.enable_incoming:
        return []

    email_sync_rule = self.build_email_sync_rule()
    try:
        email_server = self.get_incoming_server(in_receive=True, email_sync_rule=email_sync_rule)
        if self.use_imap:
            for folder in self.imap_folder:
                if email_server.select_imap_folder(folder.folder_name):
                    email_server.settings["uid_validity"] = folder.uidvalidity
                    messages = email_server.get_messages(folder=f'{folder.folder_name}') or {}
                    process_mail(messages, folder.append_to)
        else:
            messages = email_server.get_messages() or {}
            process_mail(messages)

        email_server.logout()
    except Exception:
        self.log_error(title=_("Error while connecting to email account {0}").format(self.name))
        return []

    return mails

EmailAccount.get_inbound_mails = custom_get_inbound_mails
