import frappe

no_cache = 1
allow_guest = True


def get_context(context):
    """
    Pass URL query params (machine, location) to the template so the form
    can pre-fill those fields when the client embeds the page with:
        /breakdown-report?machine=XYZ-001&location=Plant+A
    """
    context.machine = frappe.form_dict.get("machine", "")
    context.location = frappe.form_dict.get("location", "")
    context.site_url = frappe.utils.get_url()
    context.csrf_token = frappe.sessions.get_csrf_token()
    return context
