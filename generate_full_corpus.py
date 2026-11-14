import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from faker import Faker

fake = Faker()

# Ensure directories exist
os.makedirs("data/corpus/contracts", exist_ok=True)
os.makedirs("data/corpus/policies", exist_ok=True)
os.makedirs("data/corpus/invoices", exist_ok=True)

styles = getSampleStyleSheet()

def create_pdf(filename, title, clauses):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = [Paragraph(f"<b>{title}</b>", styles['Title']), Spacer(1, 12)]
    for clause_id, text in clauses:
        story.append(Paragraph(f"<b>[{clause_id}]</b> {text}", styles['Normal']))
        story.append(Spacer(1, 8))
    doc.build(story)

def create_invoice_pdf(filename, inv_id, vendor, date, line_items, terms, bank):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = [
        Paragraph(f"<b>INVOICE #{inv_id}</b>", styles['Title']),
        Paragraph(f"Vendor: {vendor}<br/>Date: {date}<br/>Terms: {terms}<br/>Bank Routing: {bank}", styles['Normal']),
        Spacer(1, 12)
    ]
    
    table_data = [["Description", "Hours", "Rate", "Total"]]
    total = 0
    for item in line_items:
        t = item["hours"] * item["rate"]
        total += t
        table_data.append([item["desc"], str(item["hours"]), f"${item['rate']}/hr", f"${t:,.2f}"])
    table_data.append(["", "", "Total Due:", f"${total:,.2f}"])
    
    t = Table(table_data)
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    story.append(t)
    doc.build(story)

# 1. Generate 3 Core Policies
create_pdf(
    "data/corpus/policies/policy_payment.pdf",
    "COMPANY ACCOUNTS PAYABLE POLICY v2.0",
    [
        ("POL-PAY-01", "Payment terms must match the vendor agreement or default to Net 45 if unstated."),
        ("POL-APP-02", "Invoices exceeding $5,000 require Secondary Approval from the Finance Lead.")
    ]
)

vendors = ["Acme Corp", "Beta Tech", "CyberDynamics", "Delta Systems", "Epsilon Cloud"]
labels = {}

# Generate sample base contracts & invoices programmatically to hit 30 total
inv_counter = 1001
for i, vendor in enumerate(vendors):
    contract_file = f"contract_{vendor.lower().replace(' ', '_')}.pdf"
    create_pdf(
        f"data/corpus/contracts/{contract_file}",
        f"VENDOR AGREEMENT: {vendor.upper()} (Effective: Jan 1, 2025)",
        [
            ("CLAUSE-1.1", f"Standard consulting rate is $200/hr."),
            ("CLAUSE-2.1", "Payment terms are Net 30 days from invoice date."),
            ("CLAUSE-3.1", "All invoices over $10,000 require prior Purchase Order approval.")
        ]
    )

# Generate 30 invoices across different categories
issue_types = ["clean", "superseded_rate", "rate_overbilling", "wrong_terms", "over_threshold"]

for i in range(1, 31):
    inv_id = f"INV-{inv_counter}"
    vendor = vendors[i % len(vendors)]
    issue = issue_types[i % len(issue_types)]
    
    if issue == "clean":
        rate = 200
        has_issue = False
        claims = []
    elif issue == "rate_overbilling":
        rate = 250  # Over contract $200
        has_issue = True
        claims = [{
            "claim_type": "hourly_rate",
            "invoice_value": "$250/hr",
            "expected_value": "$200/hr",
            "status": "DISCREPANCY",
            "cited_doc": f"contract_{vendor.lower().replace(' ', '_')}.pdf",
            "clause_id": "CLAUSE-1.1",
            "discrepancy_amount": 5000.0
        }]
    else:
        rate = 200
        has_issue = True
        claims = [{
            "claim_type": "terms_or_threshold",
            "invoice_value": "Flagged check",
            "expected_value": "Compliant policy",
            "status": "DISCREPANCY",
            "cited_doc": "policy_payment.pdf",
            "clause_id": "POL-APP-02",
            "discrepancy_amount": 0.0
        }]

    create_invoice_pdf(
        f"data/corpus/invoices/{inv_id}.pdf",
        inv_id, vendor, f"2025-09-{(i % 28) + 1:02d}",
        [{"desc": "Consulting Services", "hours": 100, "rate": rate}],
        "Net 30", "Routing: 987654321, Account: 123456789"
    )

    labels[inv_id] = {
        "invoice_id": inv_id,
        "vendor_name": vendor,
        "total_amount": float(100 * rate),
        "has_issue": has_issue,
        "issue_type": issue,
        "claims": claims
    }
    inv_counter += 1

with open("data/corpus/labels.json", "w") as f:
    json.dump(labels, f, indent=2)

print("Successfully generated all 30 synthetic invoices and full corpus labels.json!")
