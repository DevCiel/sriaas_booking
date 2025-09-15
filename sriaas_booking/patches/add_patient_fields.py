from sriaas_booking.install import _make_patient_fields, _make_status_editable

def execute():
    _make_patient_fields()
    _make_status_editable()
