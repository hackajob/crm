import frappe
from frappe import _
from frappe.email.receive import InboundMail, SentEmailInInboxError
from frappe.email.doctype.email_account.email_account import EmailAccount

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

# Custom receive method(frappe.email.doctype.email_account.email_account.EmailAccount.receive)
def custom_receive(self):
    """Called by scheduler to receive emails from this EMail account using POP3/IMAP."""
    exceptions = []
    inbound_mails = self.get_inbound_mails()
    for mail in inbound_mails:
        try:
            communication = mail.process()
            frappe.db.commit()
            if communication and mail.flags.is_new_communication:
                if self.enable_auto_reply:
                    self.send_auto_reply(communication, mail)

                # Skip sending outbound notification email
                # communication.send_email(is_inbound_mail_communcation=True)
        except SentEmailInInboxError:
            frappe.db.rollback()
        except Exception:
            frappe.db.rollback()
            try:
                self.log_error(title="EmailAccount.receive")
                if self.use_imap:
                    self.handle_bad_emails(mail.uid, mail.raw_message, frappe.get_traceback())
                exceptions.append(frappe.get_traceback())
            except Exception:
                frappe.db.rollback()
            else:
                frappe.db.commit()
        else:
            frappe.db.commit()

    if exceptions:
        raise Exception(frappe.as_json(exceptions))

EmailAccount.get_inbound_mails = custom_get_inbound_mails
EmailAccount.receive = custom_receive
