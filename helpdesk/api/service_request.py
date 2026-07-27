
import frappe
from frappe import _
from frappe.utils import today


@frappe.whitelist()
def create_service_request(
	hd_customer: str,
	subject: str,
	due_date: str,
	ticket_id: str = "",
	priority: str = "Medium",
	service_type: str = "",
):
	"""Create a Service Request from an HD Ticket.

	Automatically fills required system-level fields (company, currency,
	posting_date, status) from site defaults so callers only need to supply
	the user-facing values.
	"""

	# ── System defaults ───────────────────────────────────────────────────────
	company = frappe.defaults.get_global_default("company")
	if not company:
		frappe.throw(
			_(
				"No default Company is configured. "
				"Please set a default company in Global Defaults."
			)
		)

	currency = frappe.db.get_value("Company", company, "default_currency") or "INR"

	# ── Service Type ──────────────────────────────────────────────────────────
	# If the caller did not supply a type, fall back to the first available one.
	if not service_type:
		row = frappe.db.sql("SELECT name FROM `tabService Type` ORDER BY name LIMIT 1", as_list=True)
		service_type = row[0][0] if row else None

	if not service_type:
		frappe.throw(
			_(
				"No Service Type records found. "
				"Please create at least one Service Type before creating a Service Request."
			)
		)

	

	# ── Validate required user-facing fields ─────────────────────────────────
	if not hd_customer:
		frappe.throw(_("Customer is required."))
	if not subject:
		frappe.throw(_("Subject is required."))
	if not due_date:
		frappe.throw(_("Due Date is required."))

	# ── Create the document ───────────────────────────────────────────────────
	# Note: `customer` on Service Request is a Link to HD Customer, not ERPNext Customer.
	doc = frappe.get_doc(
		{
			"doctype": "Service Request",
			"customer_type": "HD Customer",
			"customer": hd_customer,
			"subject": subject,
			"due_date": due_date,
			"priority": priority,
			"type": service_type,
			"company": company,
			"currency": currency,
			"posting_date": today(),
			"status": "Open",
		}
	)
	doc.insert(ignore_permissions=False)

	# ── Back-link on the ticket ───────────────────────────────────────────────
	if ticket_id:
		frappe.db.set_value("HD Ticket", ticket_id, "service_request", doc.name)
		if not frappe.db.get_value("HD Ticket", ticket_id, "customer"):
			frappe.db.set_value("HD Ticket", ticket_id, "customer", hd_customer)

	return doc.as_dict()


@frappe.whitelist()
def get_service_types():
	"""Return a list of all Service Type names for the frontend selector."""
	rows = frappe.db.sql("SELECT name FROM `tabService Type` ORDER BY name", as_list=True)
	return [r[0] for r in rows]