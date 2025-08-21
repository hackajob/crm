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
						self.retrieve_message(uid, i + 1)
				except (_socket.timeout, LoginLimitExceeded):
						break

		out = {"latest_messages": self.latest_messages}
		if self.settings.use_imap:
				out.update(
						{"uid_list": email_list, "seen_status": self.seen_status, "uid_reindexed": self.uid_reindexed}
				)

		return out

EmailServer.get_messages = custom_get_messages
