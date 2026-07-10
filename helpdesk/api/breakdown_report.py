import frappe
from frappe import _


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_csrf_token() -> str:
    """
    Return the current session's CSRF token so the browser form can
    include it in the X-Frappe-CSRF-Token header of the submit POST.

    This is a safe read-only GET endpoint — it reveals no sensitive data
    beyond the token the browser already holds in its session.
    """
    return frappe.sessions.get_csrf_token()


@frappe.whitelist(allow_guest=True)
def submit(
    reporter_name: str,
    reporter_email: str,
    subject: str,
    description: str,
    machine: str = "",
    location: str = "",
) -> dict:
    """
    Create an HD Ticket from an external (guest) breakdown report form.

    The reporter is identified by email. If no Frappe User exists for that
    email, a temporary "Website User" is created so the ticket can be
    properly linked and the reporter can later track their ticket via the
    customer portal.

    Returns a dict with the new ticket name so the embed widget can show a
    confirmation message with the reference number.
    """
    _validate_inputs(reporter_name, reporter_email, subject, description)

    user_email = reporter_email.strip().lower()
    reporter_name = reporter_name.strip()

    _ensure_user(user_email, reporter_name)

    ticket_doc = _create_ticket(
        user_email=user_email,
        reporter_name=reporter_name,
        subject=subject,
        description=description,
        machine=machine,
        location=location,
    )

    return {
        "ticket_name": ticket_doc.name,
        "message": _(
            "Your breakdown report has been submitted. Reference: {0}"
        ).format(ticket_doc.name),
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_inputs(
    reporter_name: str, reporter_email: str, subject: str, description: str
) -> None:
    if not reporter_name or not reporter_name.strip():
        frappe.throw(_("Reporter name is required"), frappe.ValidationError)
    if not reporter_email or not reporter_email.strip():
        frappe.throw(_("Reporter email is required"), frappe.ValidationError)
    if not frappe.utils.validate_email_address(reporter_email):
        frappe.throw(_("Please enter a valid email address"), frappe.ValidationError)
    if not subject or not subject.strip():
        frappe.throw(_("Subject is required"), frappe.ValidationError)
    if not description or not description.strip():
        frappe.throw(_("Description is required"), frappe.ValidationError)


def _ensure_user(email: str, full_name: str) -> None:
    """
    Ensure a Frappe User exists for the reporter so the ticket raised_by
    field (which stores a user email) can be set correctly.
    Creates a Website User if one does not already exist.
    """
    if frappe.db.exists("User", email):
        return

    user = frappe.new_doc("User")
    user.email = email
    user.first_name = full_name.split(" ")[0]
    user.last_name = " ".join(full_name.split(" ")[1:]) if " " in full_name else ""
    user.full_name = full_name
    user.user_type = "Website User"
    user.send_welcome_email = 0
    user.flags.ignore_permissions = True
    user.insert(ignore_permissions=True)


def _create_ticket(
    user_email: str,
    reporter_name: str,
    subject: str,
    description: str,
    machine: str,
    location: str,
) -> "frappe.Document":
    """
    Insert an HD Ticket on behalf of the reporter.

    We run as Administrator so that the Frappe communication/SLA hooks
    (which call self.save() internally without ignore_permissions) do not
    fail under a guest or freshly-created Website User session.
    raised_by is set explicitly to the reporter's email so the ticket is
    still attributed to them correctly.
    """
    prev_user = frappe.session.user
    frappe.set_user("Administrator")

    try:
        ticket = frappe.new_doc("HD Ticket")
        ticket.subject = subject.strip()
        ticket.description = description.strip()
        ticket.raised_by = user_email
        ticket.via_customer_portal = True
        if machine:
            ticket.machine = machine.strip()
        if location:
            ticket.location = location.strip()
        ticket.insert(ignore_permissions=True)
    finally:
        frappe.set_user(prev_user)

    return ticket
