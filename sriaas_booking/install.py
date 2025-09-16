import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

MODULE_DEF_NAME = "Sriaas Booking"   # the Module Def shown in Desk
APP_PY_MODULE   = "sriaas_booking"   # your app's python package name

def after_install():
    _setup_everything()

def after_migrate():
    _setup_everything()

def _setup_everything():
    # 0) (optional) Only if you actually ship JSON files for these doctypes.
    # If you’re creating them in code, you can delete this block.
    _reload_local_json_doctypes([
        # put JSON-based doctypes here if you ship them from your app:
        # "sr_patient_disable_reason", "sr_patient_invoice_view", "sr_patient_payment_view",
    ])

    # 1) Master doctypes first (anything referenced by Link fields)
    _ensure_sr_patient_disable_reason()
    _ensure_sr_patient_invoice_view()
    _ensure_sr_patient_payment_view()
    _ensure_sr_sales_type()
    _ensure_sr_encounter_status()
    _ensure_sr_instructions()
    _ensure_sr_medication_template_item()
    _ensure_sr_medication_template()
    _ensure_sr_delivery_type()
    _ensure_sr_order_item()

    # 2) Core doctypes: add/adjust custom fields
    _make_patient_fields()
    _make_customer_fields()
    _make_address_fields()
    _make_practitioner_fields()

    # 3) Patient Encounter: base fields & sections
    _make_encounter_fields()                # your earlier Encounter fields
    _make_clinical_notes_fields()           # “Clinical Notes” section + 4 Small Text fields
    # _tune_sr_sales_type()                 # depends_on / read_only_depends_on for sr_sales_type
    _setup_ayurvedic_section()              # rename sb_drug_prescription + 3 fields under it
    _setup_homeopathy_section()
    _setup_allopathy_section()
    _setup_instructions_section()
    _setup_draft_invoice_tab()

    # 4) Housekeeping
    _apply_encounter_ui_customizations()
    _hide_encounter_flags()
    _make_status_editable()

# ----------------- utilities -----------------

def _reload_local_json_doctypes(names: list[str]):
    """Use this only if you ship DocType JSON files in your app.
       module arg MUST be the python package (e.g., 'sriaas_booking'), not the Module Def label.
    """
    for dn in names:
        try:
            frappe.reload_doc(APP_PY_MODULE, "doctype", dn)
        except Exception:
            pass

def _ps(doc_type, fieldname, prop, value, property_type):
    """Upsert a Property Setter (idempotent)."""
    name = f"{doc_type}-{fieldname}-{prop}"
    if frappe.db.exists("Property Setter", name):
        ps = frappe.get_doc("Property Setter", name)
        ps.value = value
        ps.property_type = property_type
        ps.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype":"Property Setter",
            "doctype_or_field":"DocField",
            "doc_type":doc_type,
            "field_name":fieldname,
            "property":prop,
            "value":value,
            "property_type":property_type,
            "name":name,
        }).insert(ignore_permissions=True)

def collapse_field(dt: str, fieldname: str, collapse: bool = True):
    """
    Make a Section Break collapsible/uncollapsible.
    (No-op if the field is missing.)
    """
    df = frappe.get_meta(dt).get_field(fieldname)
    if not df:
        return
    # Works best for Section Breaks; harmless otherwise.
    _ps(dt, fieldname, "collapsible", "1" if collapse else "0", "Check")

def set_field_label(dt: str, fieldname: str, new_label: str):
    """
    Change a field's label via Property Setter.
    (No-op if the field is missing.)
    """
    if not frappe.get_meta(dt).get_field(fieldname):
        return
    _ps(dt, fieldname, "label", new_label, "Data")

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

def _ensure_sr_patient_disable_reason():
    """Create SR Patient Disable Reason (master) if missing."""
    if frappe.db.exists("DocType", "SR Patient Disable Reason"):
        return

    frappe.get_doc({
        "doctype": "DocType","name": "SR Patient Disable Reason","module": MODULE_DEF_NAME,
        "custom": 0,"istable": 0,"issingle": 0,"editable_grid": 0,"track_changes": 1,"allow_rename": 0,"allow_import": 1,
        "naming_rule": "By fieldname","autoname": "field:sr_reason_name","title_field": "sr_reason_name",
        "field_order": ["sr_reason_name", "is_active", "description"],
        "fields": [
            {"fieldname": "sr_reason_name","label": "Reason Name","fieldtype": "Data","reqd": 1,"in_list_view": 1,"in_standard_filter": 1,"unique": 1,},
            {"fieldname": "is_active","label": "Is Active","fieldtype": "Check","default": "1",},
            {"fieldname": "description","label": "Description","fieldtype": "Small Text",},
        ],
        "permissions": [
            {"role": "System Manager","read": 1, "write": 1, "create": 1, "delete": 1,"print": 1, "email": 1, "export": 1,},
            {"role": "Healthcare Administrator","read": 1, "write": 1, "create": 1, "delete": 1,},
        ],
    }).insert(ignore_permissions=True)

def _ensure_sr_patient_invoice_view():
    """Create SR Patient Invoice View (child table) if missing."""
    if frappe.db.exists("DocType", "SR Patient Invoice View"):
        return

    frappe.get_doc({
        "doctype": "DocType","name": "SR Patient Invoice View","module": MODULE_DEF_NAME,
        "custom": 0,"istable": 1,"editable_grid": 1,"issingle": 0,"track_changes": 0,
        "field_order": ["sr_invoice_no","sr_posting_date","sr_grand_total", "sr_outstanding",],
        "fields": [
            {"fieldname": "sr_invoice_no","label": "Sales Invoice","fieldtype": "Link","options": "Sales Invoice","in_list_view": 1,"reqd": 0,},
            {"fieldname": "sr_posting_date","label": "Posting Date","fieldtype": "Datetime","in_list_view": 1,},
            {"fieldname": "sr_grand_total","label": "Grand Total","fieldtype": "Currency","in_list_view": 1,},
            {"fieldname": "sr_outstanding","label": "Outstanding","fieldtype": "Currency","in_list_view": 1,},
        ],
        "permissions": [],
    }).insert(ignore_permissions=True)

def _ensure_sr_patient_payment_view():
    """Create SR Patient Payment View (child table) if missing."""
    if frappe.db.exists("DocType", "SR Patient Payment View"):
        return

    frappe.get_doc({
        "doctype": "DocType","name": "SR Patient Payment View","module": MODULE_DEF_NAME,
        "custom": 0,"istable": 1,"editable_grid": 1,"issingle": 0,"track_changes": 0,
        "field_order": ["sr_payment_entry","sr_posting_date","sr_paid_amount","sr_mode_of_payment",],
        "fields": [
            {"fieldname": "sr_payment_entry","label": "Payment Entry","fieldtype": "Link","options": "Payment Entry","in_list_view": 1,},
            {"fieldname": "sr_posting_date","label": "Posting Date","fieldtype": "Datetime","in_list_view": 1,},
            {"fieldname": "sr_paid_amount","label": "Paid Amount","fieldtype": "Currency","in_list_view": 1,},
            {"fieldname": "sr_mode_of_payment","label": "Mode of Payment","fieldtype": "Data","in_list_view": 1,},
        ],
        "permissions": [],
    }).insert(ignore_permissions=True)

def _ensure_sr_sales_type():
    if not frappe.db.exists("DocType", "SR Sales Type"):
        frappe.get_doc({
            "doctype":"DocType","name":"SR Sales Type","module":MODULE_DEF_NAME,
            "naming_rule":"By fieldname","autoname":"field:sr_sales_type_name","title_field":"sr_sales_type_name",
            "field_order":["sr_sales_type_name"],
            "fields":[{"fieldname":"sr_sales_type_name","label":"Sales Type","fieldtype":"Data","reqd":1,"in_list_view":1,"unique":1}],
            "permissions":[{"role":"System Manager","read":1,"write":1,"create":1,"delete":1,"print":1,"email":1,"export":1}],
        }).insert(ignore_permissions=True)

def _ensure_sr_encounter_status():
    if not frappe.db.exists("DocType", "SR Encounter Status"):
        frappe.get_doc({
            "doctype":"DocType","name":"SR Encounter Status","module":MODULE_DEF_NAME,
            "naming_rule":"By fieldname","autoname":"field:sr_status_name","title_field":"sr_status_name",
            "field_order":["sr_status_name"],
            "fields":[{"fieldname":"sr_status_name","label":"Status Name","fieldtype":"Data","unique":1}],
            "permissions":[{"role":"System Manager","read":1,"write":1,"create":1,"delete":1,"print":1,"email":1,"export":1}],
        }).insert(ignore_permissions=True)

def _ensure_sr_instructions():
    if not frappe.db.exists("DocType", "SR Instructions"):
        frappe.get_doc({
            "doctype":"DocType","name":"SR Instructions","module":MODULE_DEF_NAME,
            "naming_rule":"By fieldname","autoname":"field:sr_title","title_field":"sr_title","track_changes":1,
            "field_order":["sr_title","sr_description"],
            "fields":[
                {"fieldname":"sr_title","label":"Title","fieldtype":"Data","reqd":1,"in_list_view":1,"unique":1},
                {"fieldname":"sr_description","label":"Description","fieldtype":"Small Text"},
            ],
            "permissions":[{"role":"System Manager","read":1,"write":1,"create":1,"delete":1,"print":1,"email":1,"export":1}],
        }).insert(ignore_permissions=True)

def _ensure_sr_medication_template_item():
    if not frappe.db.exists("DocType", "SR Medication Template Item"):
        frappe.get_doc({
            "doctype":"DocType","name":"SR Medication Template Item","module":MODULE_DEF_NAME,"istable":1,"track_changes":1,
            "field_order":["sr_medication","sr_drug_code","sr_dosage","sr_period","sr_dosage_form","sr_instruction"],
            "fields":[
                {"fieldname":"sr_medication","label":"Medication","fieldtype":"Link","options":"Medication","reqd":1,"in_list_view":1},
                {"fieldname":"sr_drug_code","label":"Drug Code","fieldtype":"Link","options":"Item"},
                {"fieldname":"sr_dosage","label":"Dosage","fieldtype":"Link","options":"Prescription Dosage","reqd":1,"in_list_view":1},
                {"fieldname":"sr_period","label":"Period","fieldtype":"Link","options":"Prescription Duration","reqd":1,"in_list_view":1},
                {"fieldname":"sr_dosage_form","label":"Dosage Form","fieldtype":"Link","options":"Dosage Form","reqd":1,"in_list_view":1},
                {"fieldname":"sr_instruction","label":"Instruction","fieldtype":"Link","options":"SR Instructions","reqd":1,"in_list_view":1},
            ],
        }).insert(ignore_permissions=True)

def _ensure_sr_medication_template():
    if not frappe.db.exists("DocType", "SR Medication Template"):
        frappe.get_doc({
            "doctype":"DocType","name":"SR Medication Template","module":MODULE_DEF_NAME,
            "naming_rule":"By fieldname","autoname":"field:sr_template_name","title_field":"sr_template_name","track_changes":1,
            "field_order":["sr_template_name","sr_instructions","sr_medications"],
            "fields":[
                {"fieldname":"sr_template_name","label":"Template Name","fieldtype":"Data","reqd":1,"in_list_view":1,"unique":1},
                {"fieldname":"sr_instructions","label":"Instructions","fieldtype":"Small Text"},
                {"fieldname":"sr_medications","label":"Medications","fieldtype":"Table","options":"SR Medication Template Item"},
            ],
            "permissions":[{"role":"System Manager","read":1,"write":1,"create":1,"delete":1,"print":1,"email":1,"export":1}],
        }).insert(ignore_permissions=True)

def _ensure_sr_delivery_type():
    """Master used by sr_delivery_type Link."""
    if frappe.db.exists("DocType", "SR Delivery Type"):
        return

    frappe.get_doc({
        "doctype": "DocType","name": "SR Delivery Type","module": MODULE_DEF_NAME,
        "naming_rule": "By fieldname","autoname": "field:sr_delivery_type_name",
        "title_field": "sr_delivery_type_name","track_changes": 1,
        "field_order": ["sr_delivery_type_name"],
        "fields": [
            {"fieldname": "sr_delivery_type_name", "label": "Delivery / Service Type","fieldtype": "Data", "reqd": 1, "unique": 1, "in_list_view": 1},
        ],
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1,"delete": 1, "print": 1, "email": 1, "export": 1}
        ],
    }).insert(ignore_permissions=True)

def _ensure_sr_order_item():
    """Child table used by Draft Invoice → Items List."""
    if frappe.db.exists("DocType", "SR Order Item"):
        return

    frappe.get_doc({
        "doctype": "DocType","name": "SR Order Item","module": MODULE_DEF_NAME,
        "custom": 0,"istable": 1,"editable_grid": 1,"issingle": 0,"track_changes": 1,
        "field_order": [
            "sr_item_code", "sr_item_name", "sr_item_description",
            "sr_item_uom", "sr_item_qty", "sr_item_rate", "sr_item_amount"
        ],
        "fields": [
            {"fieldname": "sr_item_code", "label": "Item","fieldtype": "Link", "options": "Item", "reqd": 1, "in_list_view": 1},
            {"fieldname": "sr_item_name", "label": "Item Name","fieldtype": "Data", "read_only": 1, "fetch_from": "sr_item_code.item_name"},
            {"fieldname": "sr_item_description", "label": "Description","fieldtype": "Small Text"},
            {"fieldname": "sr_item_uom", "label": "UOM","fieldtype": "Link", "options": "UOM", "in_list_view": 1},
            {"fieldname": "sr_item_qty", "label": "Qty","fieldtype": "Float", "in_list_view": 1, "default": 1},
            {"fieldname": "sr_item_rate", "label": "Rate","fieldtype": "Currency", "in_list_view": 1},
            {"fieldname": "sr_item_amount", "label": "Amount","fieldtype": "Currency", "in_list_view": 1, "read_only": 1},
        ],
        "permissions": [],
    }).insert(ignore_permissions=True)

def _make_patient_fields():
    """Adds custom fields & tabs to Patient DocType.
    NOTE:
      - Ensure the following DocTypes exist in your system:
          • Medical Department (standard in Healthcare)
          • SR Patient Disable Reason (Disable Reason DocType)
          • SR Patient Invoice View (Child Table DocType)
          • SR Patient Payment View (Child Table DocType)
      - 'Patient Encounter' is standard in Healthcare.
    """
    patient_custom_fields = {
        "Patient": [
            # --- DETAILS TAB ---
            {"fieldname": "sr_medical_department","label": "Department","fieldtype": "Link","options": "Medical Department","insert_after": "patient_name"},
            {"fieldname": "sr_patient_id","label": "Patient ID","fieldtype": "Data","insert_after": "sr_medical_department"},
            {"fieldname": "sr_practo_id","label": "Practo ID","fieldtype": "Data","insert_after": "sr_patient_id"},
            {"fieldname": "sr_patient_age","label": "Patient Age","fieldtype": "Data","insert_after": "age_html"},
            {"fieldname": "sr_followup_disable_reason","label": "Followup Disable Reason","fieldtype": "Link","options": "SR Patient Disable Reason","insert_after": "status"},
            {"fieldname": "sr_followup_status","label": "Followup Status","fieldtype": "Select","options": "\nPending\nDone","insert_after": "user_id"},

            # --- INVOICES TAB ---
            {"fieldname": "sr_invoices_tab","label": "Invoices","fieldtype": "Tab Break","insert_after": "other_risk_factors"},
            {"fieldname": "sr_sales_invoice_list","label": "Sales Invoices","fieldtype": "Table","options": "SR Patient Invoice View","read_only": 1,"insert_after": "sr_invoices_tab"},

            # --- PAYMENTS TAB ---
            {"fieldname": "sr_payments_tab","label": "Payments","fieldtype": "Tab Break","insert_after": "sr_sales_invoice_list"},
            {"fieldname": "sr_payment_entry_list","label": "Payment Entries","fieldtype": "Table","options": "SR Patient Payment View", "read_only": 1,"insert_after": "sr_payments_tab"},

            # --- PEX TAB (Patient Encounters) ---
            {"fieldname": "sr_pex_tab","label": "Patient Encounters","fieldtype": "Tab Break","insert_after": "sr_payment_entry_list"},
            {"fieldname": "sr_pex_launcher_html","label": "PE Launcher","fieldtype": "HTML","read_only": 1,"insert_after": "sr_pex_tab"},
            {"fieldname": "sr_last_created_pe","label": "Last Created Patient Encounter","fieldtype": "Link","options": "Patient Encounter","insert_after": "sr_pex_launcher_html"},

            # --- FOLLOWUP MARKER TAB ---
            {"fieldname": "sr_followup_marker_tab","label": "Follow-up Marker","fieldtype": "Tab Break","insert_after": "sr_last_created_pe"},
            {"fieldname": "sr_followup_day","label": "Follow-up Day","fieldtype": "Select","options": "\nMon\nTue\nWed\nThu\nFri\nSat","insert_after": "sr_followup_marker_tab"},
            {"fieldname": "sr_followup_id","label": "Follow-up ID","fieldtype": "Select","options": "\n0\n1\n2\n3\n4\n5\n6\n7\n8\n9","insert_after": "sr_followup_day"},
        ]
    }
    create_custom_fields(patient_custom_fields, ignore_validate=True)

def _make_customer_fields():
    # 1) Customer custom field
    customer_custom_fields = {
        "Customer": [{
            "fieldname": "sr_customer_id",
            "label": "Customer ID",
            "fieldtype": "Data",
            "insert_after": "salutation",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "unique": 1,
        }]
    }
    create_custom_fields(customer_custom_fields, ignore_validate=True)

def _make_address_fields():
    _upsert_property_setter("Address", "is_primary_address", "default", "1", "Text")
    _upsert_property_setter("Address", "is_shipping_address", "default", "1", "Text")

def _make_practitioner_fields():
    practitioner_custom_fields = {
        "Healthcare Practitioner": [
            {"fieldname": "sr_reg_no", "label": "Registration No", "fieldtype": "Data", "insert_after": "office_phone"},
            {"fieldname": "sr_qualification", "label": "Qualification", "fieldtype": "Data", "reqd": 1, "insert_after": "sr_reg_no"},
            {"fieldname": "sr_college_university", "label": "College/University", "fieldtype": "Data", "insert_after": "sr_qualification"},
            {"fieldname": "sr_pathy", "label": "Pathy", "fieldtype": "Select",
             "options": "\nAyurveda\nHomeopathy\nAllopathy", "in_list_view": 1, "in_standard_filter": 1,
             "insert_after": "practitioner_type"},
        ]
    }
    create_custom_fields(practitioner_custom_fields, ignore_validate=True)

def _make_encounter_fields():
    lead_source_dt = "CRM Lead Source" if frappe.db.exists("DocType","CRM Lead Source") else "Lead Source"

    encounter_custom_fields = {
        "Patient Encounter": [
            {"fieldname":"sr_encounter_type","label":"Encounter Type","fieldtype":"Select",
             "options":"\nFollowup\nOrder","reqd":1,"in_list_view":1,"in_standard_filter":1,"allow_on_submit":1,
             "insert_after":"naming_series"},

            {"fieldname":"sr_encounter_place","label":"Encounter Place","fieldtype":"Select",
             "options":"\nOnline\nOPD","reqd":1,"in_list_view":1,"in_standard_filter":1,
             "insert_after":"sr_encounter_type"},

            {"fieldname":"sr_sales_type","label":"Sales Type","fieldtype":"Link","options":"SR Sales Type",
             "insert_after":"sr_encounter_place","depends_on": 'eval:doc.sr_encounter_type=="Order"',"mandatory_depends_on": 'eval:doc.sr_encounter_type=="Order"'},

            {"fieldname":"sr_pe_mobile","label":"Patient Mobile","fieldtype":"Data","read_only":1,
             "depends_on":"eval:doc.patient","fetch_from":"patient.mobile","in_list_view":1,"in_standard_filter":1,
             "insert_after":"inpatient_status"},

            {"fieldname":"sr_pe_id","label":"Patient ID","fieldtype":"Data","read_only":1,
             "depends_on":"eval:doc.patient","fetch_from":"patient.sr_patient_id","in_list_view":1,"in_standard_filter":1,
             "insert_after":"sr_pe_mobile"},

            {"fieldname":"sr_pe_deptt","label":"Patient Department","fieldtype":"Data","read_only":1,
             "depends_on":"eval:doc.patient","fetch_from":"patient.sr_medical_department","in_list_view":1,"in_standard_filter":1,
             "insert_after":"sr_pe_id"},

            {"fieldname":"sr_pe_age","label":"Patient Age","fieldtype":"Data","read_only":1,
             "depends_on":"eval:doc.patient","fetch_from":"patient.sr_patient_age","in_list_view":1,"in_standard_filter":1,
             "insert_after":"sr_pe_deptt"},

            {"fieldname":"sr_encounter_source","label":"Encounter Source","fieldtype":"Link",
             "options": lead_source_dt, "reqd":1, "insert_after":"google_meet_link"},

            {"fieldname":"sr_encounter_status","label":"Encounter Status","fieldtype":"Link",
             "options":"SR Encounter Status","in_list_view":1,"in_standard_filter":1,"allow_on_submit":1,
             "insert_after":"sr_encounter_source"},
        ]
    }
    create_custom_fields(encounter_custom_fields, ignore_validate=True)

def _make_clinical_notes_fields():
    create_custom_fields({
        "Patient Encounter": [
            {"fieldname":"sr_clinical_notes_sb","label":"Clinical Notes","fieldtype":"Section Break","collapsible":1,"insert_after":"submit_orders_on_save"},
            {"fieldname":"sr_complaints","label":"Complaints","fieldtype":"Small Text","insert_after":"sr_clinical_notes_sb"},
            {"fieldname":"sr_observations","label":"Observations","fieldtype":"Small Text","insert_after":"sr_complaints"},
            {"fieldname":"sr_investigations","label":"Investigations","fieldtype":"Small Text","insert_after":"sr_observations"},
            {"fieldname":"sr_notes","label":"Notes","fieldtype":"Small Text","insert_after":"sr_investigations"},
        ]
    }, ignore_validate=True)

def _setup_ayurvedic_section():
    dt = "Patient Encounter"
    _ps(dt, "sb_drug_prescription", "label", "Ayurvedic Medications", "Data")
    _ps(dt, "sb_drug_prescription", "collapsible", "1", "Check")
    _ps(dt, "drug_prescription", "label", "Ayurvedic Drug Prescription", "Data")

    hp_meta = frappe.get_meta("Healthcare Practitioner")
    name_field = "practitioner_name" if hp_meta.get_field("practitioner_name") else (
        "full_name" if hp_meta.get_field("full_name") else "practitioner_name"
    )

    create_custom_fields({
        dt: [
            {"fieldname":"sr_medication_template","label":"Medication Template","fieldtype":"Link","options":"SR Medication Template","insert_after":"sb_drug_prescription"},
            {"fieldname":"sr_ayurvedic_practitioner","label":"Ayurvedic Practitioner","fieldtype":"Link","options":"Healthcare Practitioner","insert_after":"sr_medication_template"},
            {"fieldname":"sr_ayurvedic_practitioner_name","label":"Ayurvedic Practitioner Name","fieldtype":"Data","read_only":1,"fetch_from":f"sr_ayurvedic_practitioner.{name_field}","insert_after":"sr_ayurvedic_practitioner"},
        ]
    }, ignore_validate=True)

def _setup_homeopathy_section():
    dt = "Patient Encounter"
    hp_meta = frappe.get_meta("Healthcare Practitioner")
    name_field = "practitioner_name" if hp_meta.get_field("practitioner_name") else (
        "full_name" if hp_meta.get_field("full_name") else "practitioner_name"
    )

    create_custom_fields({
        dt: [
            {
                "fieldname": "sr_homeopathy_medications_sb",
                "label": "Homeopathy Medications",
                "fieldtype": "Section Break",
                "collapsible": 1,
                "insert_after": "drug_prescription",
            },
            {
                "fieldname": "sr_homeopathy_practitioner",
                "label": "Homeopathy Practitioner",
                "fieldtype": "Link",
                "options": "Healthcare Practitioner",
                "insert_after": "sr_homeopathy_medications_sb",
            },
            {
                "fieldname": "sr_homeopathy_practitioner_name",
                "label": "Homeopathy Practitioner Name",
                "fieldtype": "Data",
                "read_only": 1,
                "fetch_from": f"sr_homeopathy_practitioner.{name_field}",
                "insert_after": "sr_homeopathy_practitioner",
            },
            {
                "fieldname": "sr_homeopathy_drug_prescription",
                "label": "Homeopathy Drug Prescription",
                "fieldtype": "Table",
                "options": "Drug Prescription",
                "allow_on_submit": 1,
                "insert_after": "sr_homeopathy_practitioner_name",
            },
        ]
    }, ignore_validate=True)

def _setup_allopathy_section():
    dt = "Patient Encounter"
    hp_meta = frappe.get_meta("Healthcare Practitioner")
    name_field = "practitioner_name" if hp_meta.get_field("practitioner_name") else (
        "full_name" if hp_meta.get_field("full_name") else "practitioner_name"
    )

    create_custom_fields({
        dt: [
            {
                "fieldname": "sr_allopathy_medications_sb",
                "label": "Allopathy Medications",
                "fieldtype": "Section Break",
                "collapsible": 1,
                "insert_after": "sr_homeopathy_drug_prescription",
            },
            {
                "fieldname": "sr_allopathy_practitioner",
                "label": "Allopathy Practitioner",
                "fieldtype": "Link",
                "options": "Healthcare Practitioner",
                "insert_after": "sr_allopathy_medications_sb",
            },
            {
                "fieldname": "sr_allopathy_practitioner_name",
                "label": "Allopathy Practitioner Name",
                "fieldtype": "Data",
                "read_only": 1,
                "fetch_from": f"sr_allopathy_practitioner.{name_field}",
                "insert_after": "sr_allopathy_practitioner",
            },
            {
                "fieldname": "sr_allopathy_drug_prescription",
                "label": "Allopathy Drug Prescription",
                "fieldtype": "Table",
                "options": "Drug Prescription",
                "allow_on_submit": 1,
                "insert_after": "sr_allopathy_practitioner_name",
            },
        ]
    }, ignore_validate=True)

def _setup_instructions_section():
    dt = "Patient Encounter"
    create_custom_fields({
        dt: [
            {
                "fieldname": "sr_instructions_sb",
                "label": "Instructions",
                "fieldtype": "Section Break",
                "collapsible": 1,
                "insert_after": "sr_allopathy_drug_prescription",
            },
            {
                "fieldname": "sr_instructions_item",
                "label": "Instructions",
                "fieldtype": "Small Text",
                "insert_after": "sr_instructions_sb",
            },
        ]
    }, ignore_validate=True)

def _setup_draft_invoice_tab():
    dt = "Patient Encounter"

    create_custom_fields({
        dt: [
            # Tab visible only for Encounter Type = Order
            {"fieldname": "sr_draft_invoice_tab", "label": "Draft Invoice","fieldtype": "Tab Break", "insert_after": "clinical_notes","depends_on": 'eval:doc.sr_encounter_type=="Order"'},

            # Delivery Type (required only in Order context)
            {"fieldname": "sr_delivery_type", "label": "Delivery Type","fieldtype": "Link", "options": "SR Delivery Type","insert_after": "sr_draft_invoice_tab","depends_on": 'eval:doc.sr_encounter_type=="Order"',"mandatory_depends_on": 'eval:doc.sr_encounter_type=="Order"'},

            # --- Items List ---
            {"fieldname": "sr_items_list_sb", "label": "Items List","fieldtype": "Section Break", "collapsible": 0,"insert_after": "sr_delivery_type"},
            {"fieldname": "sr_pe_order_items", "label": "Order Items","fieldtype": "Table", "options": "SR Order Item","insert_after": "sr_items_list_sb"},

            # --- Advance Payment ---
            {"fieldname": "sr_advance_payment_sb", "label": "Advance Payment","fieldtype": "Section Break", "collapsible": 0,"insert_after": "sr_pe_order_items"},
            {"fieldname": "sr_pe_mode_of_payment", "label": "Mode of Payment","fieldtype": "Link", "options": "Mode of Payment","insert_after": "sr_advance_payment_sb"},
            {"fieldname": "sr_pe_paid_amount", "label": "Paid Amount","fieldtype": "Currency","insert_after": "sr_pe_mode_of_payment"},

            # --- Payment Receipt ---
            {"fieldname": "sr_payment_receipt_sb", "label": "Payment Receipt","fieldtype": "Section Break", "collapsible": 1,"insert_after": "sr_pe_paid_amount"},
            {"fieldname": "sr_pe_payment_reference_no", "label": "Payment Reference No","fieldtype": "Data", "insert_after": "sr_payment_receipt_sb"},
            {"fieldname": "sr_pe_payment_reference_date", "label": "Payment Reference Date","fieldtype": "Date", "insert_after": "sr_pe_payment_reference_no"},
            {"fieldname": "sr_pe_payment_proof", "label": "Payment Proof","fieldtype": "Attach Image", "insert_after": "sr_pe_payment_reference_date"},
        ]
    }, ignore_validate=True)

def _apply_encounter_ui_customizations():
    dt = "Patient Encounter"

    # Collapse these sections
    for f in ["sb_symptoms", "sb_test_prescription", "sb_procedures","rehabilitation_section", "section_break_33"]:
        collapse_field(dt, f, True)

    # Rename section_break_33 → "Review"
    set_field_label(dt, "section_break_33", "Review")

def _hide_encounter_flags():
    """Hide core Patient Encounter fields: invoiced, submit_orders_on_save, codification_table, symptoms, diagnosis."""
    targets = ("invoiced", "submit_orders_on_save","codification_table", "symptoms", "diagnosis","procedure_prescription","therapy_plan","therapies","naming_series","appointment")
    for f in targets:
        # If someone made it a Custom Field, update that; else use Property Setter
        cfname = frappe.db.get_value("Custom Field", {"dt":"Patient Encounter","fieldname":f}, "name")
        if cfname:
            cf = frappe.get_doc("Custom Field", cfname)
            cf.hidden = 1
            cf.in_list_view = 0
            cf.in_standard_filter = 0
            cf.save(ignore_permissions=True)
        else:
            _ps("Patient Encounter", f, "hidden", "1", "Check")
            _ps("Patient Encounter", f, "in_list_view", "0", "Check")
            _ps("Patient Encounter", f, "in_standard_filter", "0", "Check")

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
