import frappe
from frappe import _

# Import helpers from Frappe's SMS Settings module
from frappe.core.doctype.sms_settings.sms_settings import (
    get_headers,
    send_request,
    create_sms_log,
)

# Keep a handle to the original function (for potential rebinds)
from frappe.core.doctype.sms_settings import sms_settings as _frappe_sms_module

_original_fn = getattr(_frappe_sms_module, "send_via_gateway", None)


def _get_user_from_number(user: str) -> str | None:
    """Resolve a per-user From number from CRM Telephony Agent.

    Preference order:
    - twilio_number
    - exotel_number
    - mobile_no
    Returns None if nothing set.
    """
    if not user:
        return None

    for field in ("twilio_number", "exotel_number", "mobile_no"):
        try:
            num = frappe.db.get_value("CRM Telephony Agent", user, field)
            if num:
                return num
        except Exception:
            # ignore and try next field
            pass
    return None


def custom_send_via_gateway(arg):
    """Override of Frappe's send_via_gateway.

    Injects user-specific 'From' number from CRM Telephony Agent, overriding any
    static 'From' configured in SMS Settings parameters.
    """
    ss = frappe.get_doc("SMS Settings", "SMS Settings")
    headers = get_headers(ss)
    use_json = headers.get("Content-Type") == "application/json"

    message = frappe.safe_decode(arg.get("message"))
    args = {ss.message_parameter: message}

    # Add non-header static params from SMS Settings
    for d in ss.get("parameters"):
        if not d.header:
            args[d.parameter] = d.value

    # Resolve per-user 'From' from CRM Telephony Agent
    from_number = _get_user_from_number(frappe.session.user)
    if from_number:
        args["From"] = from_number
    else:
        frappe.logger().info(
            f"[CRM] No user-specific From number for {frappe.session.user}; using default"
        )

    success_list = []
    for d in arg.get("receiver_list"):
        args[ss.receiver_parameter] = d
        status = send_request(ss.sms_gateway_url, args, headers, ss.use_post, use_json)
        if 200 <= status < 300:
            success_list.append(d)

    if success_list:
        args.update(arg)
        create_sms_log(args, success_list)
        if arg.get("success_msg"):
            frappe.msgprint(_("SMS sent successfully"))
