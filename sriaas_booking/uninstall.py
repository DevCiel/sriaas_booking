import frappe

FIELD_PREFIX = "sr_"  # all your fields use this prefix
TARGET_DTS = [
    "Patient",
    "Customer",
    "Address",
    "Healthcare Practitioner",
    "Patient Encounter",
]

# Property Setters that changed *standard* fields we should revert
PS_EXTRAS = [
    # Patient
    ("Patient", "status", "read_only"),
    ("Patient", "status", "read_only_depends_on"),

    # Address defaults you set
    ("Address", "is_primary_address", "default"),
    ("Address", "is_shipping_address", "default"),

    # Patient Encounter — various label/visibility/collapsible tweaks
    ("Patient Encounter", "drug_prescription", "label"),
    ("Patient Encounter", "sb_drug_prescription", "label"),
    ("Patient Encounter", "codification_table", "hidden"),
    ("Patient Encounter", "symptoms", "hidden"),
    ("Patient Encounter", "diagnosis", "hidden"),
    ("Patient Encounter", "sb_symptoms", "collapsible"),
    ("Patient Encounter", "sb_test_prescription", "collapsible"),
    ("Patient Encounter", "sb_procedures", "collapsible"),
    ("Patient Encounter", "rehabilitation_section", "collapsible"),
    ("Patient Encounter", "section_break_33", "collapsible"),
    ("Patient Encounter", "section_break_33", "label"),  # "Review"
]

def before_uninstall():
    """Remove Custom Fields & Property Setters introduced by this app."""
    _remove_custom_fields()
    _remove_property_setters()
    frappe.clear_cache()

def _remove_custom_fields():
    # Delete all Custom Fields that start with your prefix on the target doctypes
    for dt in TARGET_DTS:
        names = frappe.get_all(
            "Custom Field",
            filters={"dt": dt, "fieldname": ["like", f"{FIELD_PREFIX}%"]},
            pluck="name",
        )
        for name in names:
            try:
                frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=1)
            except Exception as e:
                frappe.log_error(f"Uninstall: failed deleting Custom Field {name}: {e}")

def _remove_property_setters():
    # 1) Any PS tied to your prefixed fields
    ps_names = frappe.get_all(
        "Property Setter",
        filters={"field_name": ["like", f"{FIELD_PREFIX}%"]},
        pluck="name",
    )
    # 2) Specific PS that touch standard fields (labels/hidden/collapsible/etc.)
    for dt, fn, prop in PS_EXTRAS:
        name = f"{dt}-{fn}-{prop}"
        if frappe.db.exists("Property Setter", name):
            ps_names.append(name)

    for name in set(ps_names):
        try:
            frappe.delete_doc("Property Setter", name, ignore_permissions=True, force=1)
        except Exception as e:
            frappe.log_error(f"Uninstall: failed deleting Property Setter {name}: {e}")
