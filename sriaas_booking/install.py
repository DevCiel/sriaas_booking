import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def after_install():
    _make_patient_fields()
    _make_status_editable()

def after_migrate():
    MODULE = "Sriaas Booking"  # this is the Module Def name
    for dn in ("sr_patient_disable_reason", "sr_patient_invoice_view", "sr_patient_payment_view"):
        try:
            frappe.reload_doc(MODULE, "doctype", dn)
        except Exception:
            pass
    _make_patient_fields()
    _make_status_editable()

def _make_patient_fields():
    """
    Adds custom fields & tabs to Patient DocType.
    NOTE:
      - Ensure the following DocTypes exist in your system:
          • Medical Department (standard in Healthcare)
          • SR Patient Disable Reason (Disable Reason DocType)
          • SR Patient Invoice View (Child Table DocType)
          • SR Patient Payment View (Child Table DocType)
      - 'Patient Encounter' is standard in Healthcare.
    """

    custom_fields = {
        "Patient": [

            # --- DETAILS TAB (no new Tab Break; placed after core 'first_name') ---
            {
                "fieldname": "sr_medical_department",
                "label": "Department",
                "fieldtype": "Link",
                "options": "Medical Department",
                "insert_after": "patient_name"
            },
            {
                "fieldname": "sr_patient_id",
                "label": "Patient ID",
                "fieldtype": "Data",
                "insert_after": "sr_medical_department"
            },
            {
                "fieldname": "sr_practo_id",
                "label": "Practo ID",
                "fieldtype": "Data",
                "insert_after": "sr_patient_id"
            },
            {
                "fieldname": "sr_patient_age",
                "label": "Patient Age",
                "fieldtype": "Data",
                "insert_after": "age_html"
            },
            # Make core 'status' editable via Property Setter (done below).
            {
                "fieldname": "sr_followup_disable_reason",
                "label": "Followup Disable Reason",
                "fieldtype": "Link",
                "options": "SR Patient Disable Reason",
                "insert_after": "status"
            },
            {
                "fieldname": "sr_followup_status",
                "label": "Followup Status",
                "fieldtype": "Select",
                "options": "\nPending\nDone",
                "insert_after": "user_id"
            },

            # --- INVOICES TAB ---
            {
                "fieldname": "sr_invoices_tab",
                "label": "Invoices",
                "fieldtype": "Tab Break",
                "insert_after": "other_risk_factors"
            },
            {
                "fieldname": "sr_sales_invoice_list",
                "label": "Sales Invoices",
                "fieldtype": "Table",
                "options": "SR Patient Invoice View",  # child table doctype
                "read_only": 1,
                "insert_after": "sr_invoices_tab"
            },

            # --- PAYMENTS TAB ---
            {
                "fieldname": "sr_payments_tab",
                "label": "Payments",
                "fieldtype": "Tab Break",
                "insert_after": "sr_sales_invoice_list"
            },
            {
                "fieldname": "sr_payment_entry_list",
                "label": "Payment Entries",
                "fieldtype": "Table",
                "options": "SR Patient Payment View",  # child table doctype
                "read_only": 1,
                "insert_after": "sr_payments_tab"
            },

            # --- PEX TAB (Patient Encounters) ---
            {
                "fieldname": "sr_pex_tab",
                "label": "Patient Encounters",
                "fieldtype": "Tab Break",
                "insert_after": "sr_payment_entry_list"
            },
            {
                "fieldname": "sr_pex_launcher_html",
                "label": "PE Launcher",
                "fieldtype": "HTML",
                "read_only": 1,
                "insert_after": "sr_pex_tab"
            },
            {
                "fieldname": "sr_last_created_pe",
                "label": "Last Created Patient Encounter",
                "fieldtype": "Link",
                "options": "Patient Encounter",
                "insert_after": "sr_pex_launcher_html"
            },

            # --- FOLLOWUP MARKER TAB ---
            {
                "fieldname": "sr_followup_marker_tab",
                "label": "Follow-up Marker",
                "fieldtype": "Tab Break",
                "insert_after": "sr_last_created_pe"
            },
            {
                "fieldname": "sr_followup_day",
                "label": "Follow-up Day",
                "fieldtype": "Select",
                "options": "\nMon\nTue\nWed\nThu\nFri\nSat",
                "insert_after": "sr_followup_marker_tab"
            },
            {
                "fieldname": "sr_followup_id",
                "label": "Follow-up ID",
                "fieldtype": "Select",
                "options": "\n0\n1\n2\n3\n4\n5\n6\n7\n8\n9",
                "insert_after": "sr_followup_day"
            },
        ]
    }

    # Create / update
    create_custom_fields(custom_fields, ignore_validate=True)

def _make_status_editable():
    """Make core Patient.status editable (remove read-only)."""
    _upsert_property_setter(
        doctype="Patient",
        fieldname="status",
        prop="read_only",
        value="0",
        property_type="Check",
    )
    # In case the doctype had a dependency making it read-only, clear it
    _upsert_property_setter(
        doctype="Patient",
        fieldname="status",
        prop="read_only_depends_on",
        value="",
        property_type="Text",
    )

def _upsert_property_setter(doctype, fieldname, prop, value, property_type):
    name = f"{doctype}-{fieldname}-{prop}"
    if frappe.db.exists("Property Setter", name):
        ps = frappe.get_doc("Property Setter", name)
        ps.value = value
        ps.property_type = property_type
        ps.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": doctype,
            "field_name": fieldname,
            "property": prop,
            "value": value,
            "property_type": property_type,
            "name": name,
        }).insert(ignore_permissions=True)
