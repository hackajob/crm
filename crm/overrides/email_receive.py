import _socket
from frappe.email.receive import EmailServer
from frappe.utils import cint
from frappe.email.receive import LoginLimitExceeded

def custom_get_messages(self, folder="INBOX"):
		"""Returns new email messages with improved sync logic."""
		self.latest_messages = []
		self.seen_status = {}
		self.uid_reindexed = False

		email_list = self.get_new_mails(folder)
		num = len(email_list)

		# reindexed or initial sync
		if self.uid_reindexed and num > cint(self.settings.initial_sync_count):
				# sort so that the most recent uid is on top
				email_list.reverse()
				email_list = email_list[:cint(self.settings.initial_sync_count)]
				email_list.reverse()

		if num > 100:
				num = 100

		for i, uid in enumerate(email_list[:num]):
				try:
						self.retrieve_message(uid, i + 1, folder)
				except (_socket.timeout, LoginLimitExceeded):
						break

		out = {"latest_messages": self.latest_messages}
		if self.settings.use_imap:
				out.update(
						{"uid_list": email_list, "seen_status": self.seen_status, "uid_reindexed": self.uid_reindexed}
				)

		return out

def custom_check_imap_uidvalidity(self, folder):
		# compare the UIDVALIDITY of email account and imap server
		uid_validity = cint(self.settings.uid_validity)

		response, message = self.imap.status(folder, "(UIDVALIDITY UIDNEXT)")
		current_uid_validity = cint(self.parse_imap_response("UIDVALIDITY", message[0]))

		uidnext = int(self.parse_imap_response("UIDNEXT", message[0]) or "1")

		if uid_validity is None:
			frappe.flags.initial_sync = True

		if not uid_validity or uid_validity != current_uid_validity:
			# uidvalidity changed & all email uids are reindexed by server
			Communication = frappe.qb.DocType("Communication")
			frappe.qb.update(Communication).set(Communication.uid, -1).where(
				Communication.communication_medium == "Email"
			).where(Communication.email_account == self.settings.email_account).run()

			# new update for the IMAP Folder DocType
			IMAPFolder = frappe.qb.DocType("IMAP Folder")
			frappe.qb.update(IMAPFolder).set(IMAPFolder.uidvalidity, current_uid_validity).set(
				IMAPFolder.uidnext, uidnext
			).where(IMAPFolder.parent == self.settings.email_account_name).where(
				IMAPFolder.folder_name == folder
			).run()

			self.settings.email_sync_rule = "ALL"
			self.uid_reindexed = True

EmailServer.get_messages = custom_get_messages
EmailServer.check_imap_uidvalidity = custom_check_imap_uidvalidity