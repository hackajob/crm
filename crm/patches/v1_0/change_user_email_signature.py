import frappe

def execute():
    # Check if property setter already exists
    if not frappe.db.exists("Property Setter", {
        "doc_type": "User",
        "field_name": "email_signature",
        "property": "fieldtype"
    }):
        frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": "User",
            "doctype_or_field": "DocField",
            "field_name": "email_signature",
            "property": "fieldtype",
            "value": "Text Editor"
        }).insert()
