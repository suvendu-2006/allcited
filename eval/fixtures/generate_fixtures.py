from pathlib import Path

import pymupdf as fitz


def create_handbook_pdf(output_path: str):
    doc = fitz.open()

    pages_data = [
        # Page 1: Introduction and Organization Structure
        [
            ("Allcited Corporate Employee Handbook", 22, True),
            ("1. General Employment Framework", 16, True),
            (
                "Welcome to Allcited. This employee handbook sets out the official terms, rules, and conditions "
                "governing all full-time, part-time, and contract personnel across all operating divisions. "
                "Compliance with all company directives and procedural guidelines is mandatory.",
                11,
                False,
            ),
            ("1.1 Scope and Application", 13, True),
            (
                "This policy applies globally to all employees, consultants, and directors. Specific regional addenda "
                "may provide additional statutory protections where required by municipal labor legislation.",
                11,
                False,
            ),
            ("1.2 Code of Business Conduct", 13, True),
            (
                "Every team member must act with absolute integrity, transparency, and professional diligence. "
                "Conflicts of interest must be formally declared to the ethics committee under procedure EC-101.",
                11,
                False,
            ),
        ],
        # Page 2: Leave & Absence Policies (Contains cross-references and rules)
        [
            ("2. Leave and Time-Off Entitlements", 16, True),
            (
                "The organization provides comprehensive leave arrangements designed to support employee well-being, "
                "rest, health recovery, and family obligations.",
                11,
                False,
            ),
            ("2.1 Annual Paid Leave", 13, True),
            (
                "Full-time employees accrue 24 days of paid annual leave per calendar year, calculated at the rate "
                "of 2.0 working days for every completed month of active service.",
                11,
                False,
            ),
            ("Rule 2.1.4 Carry-Forward Restrictions", 12, True),
            (
                "A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year. "
                "Any surplus beyond 8 days will automatically lapse on March 31 unless granted an executive waiver.",
                11,
                False,
            ),
            ("2.2 Sick and Medical Leave", 13, True),
            (
                "Staff members are eligible for 12 days of paid sick leave annually. Absences exceeding two consecutive "
                "working days require a medical practitioner certificate submitted via Form HR-702.",
                11,
                False,
            ),
            ("Rule 2.2.9 Critical Illness Coverage", 12, True),
            (
                "In instances of prolonged hospitalization, employees may draw down extended disability pay as "
                "stipulated in medical schedule MS-4.",
                11,
                False,
            ),
        ],
        # Page 3: Resignation, Separation & Cross-References (P3 / P4 scenarios)
        [
            ("3. Separation, Resignation and Exit Terms", 16, True),
            (
                "This section outlines notice periods, property return, and financial settlements upon termination "
                "or voluntary resignation.",
                11,
                False,
            ),
            ("3.1 Voluntary Resignation and Notice Period", 13, True),
            (
                "Permanent employees who wish to terminate their employment agreement must tender formal written notice "
                "at least 60 calendar days in advance to their designated reporting officer.",
                11,
                False,
            ),
            ("3.2 Leave Settlement on Departure", 13, True),
            (
                "All accrued but unutilized annual leave will be settled in the final paycheck as per rule 63.7.4. "
                "Employees under active notice may not take paid leave without the written authorization of the Vice President of HR.",
                11,
                False,
            ),
            ("3.3 Exit Handover Protocols", 13, True),
            (
                "All corporate computing assets, access cards, and confidential proprietary material must be surrendered "
                "to the department supervisor on the final working day.",
                11,
                False,
            ),
        ],
        # Page 4: Technical & Equipment Guidelines + Statutory Rules
        [
            ("4. Information Technology and Security", 16, True),
            (
                "Company-issued electronic devices, networks, credentials, and software are restricted exclusively to authorized "
                "business usage.",
                11,
                False,
            ),
            ("Clause 4.2 Security Credential Protocols", 13, True),
            (
                "Multi-factor authentication (MFA) is strictly mandatory on all internal systems. Passwords must be at least "
                "16 characters in length and refreshed every 90 days as mandated by standard ISO-27001.",
                11,
                False,
            ),
            ("Clause 5.1 Remote Work Policy", 13, True),
            (
                "Employees authorized for remote work must maintain a private, secure workspace. Public unsecured Wi-Fi "
                "connections without VPN encapsulation are strictly prohibited.",
                11,
                False,
            ),
            ("5. Statutory Schedules and Specialized Rules", 16, True),
            ("Rule 63.7.4 Leave Encashment on Resignation", 12, True),
            (
                "Upon voluntary resignation or formal separation, accrued annual leave days up to a cap of 30 working days "
                "shall be encashed at the employee base salary daily rate, computed as monthly basic pay divided by 22 working days. "
                "Sick leave, compassionate leave, and floating holidays are strictly non-encashable and non-transferable.",
                11,
                False,
            ),
        ],
        # Page 5: Working Hours and Overtime Matrix
        [
            ("6. Employee Working Hours and Scheduling", 16, True),
            (
                "Standard operational work hours for full-time personnel comprise 40 hours per week, typically scheduled "
                "from 09:00 to 18:00 local business time with one hour for lunch.",
                11,
                False,
            ),
            ("6.1 Core Collaboration Windows", 13, True),
            (
                "All team members, regardless of approved flexible arrangements, must remain available during the mandatory "
                "core coordination window between 10:00 and 16:00 daily.",
                11,
                False,
            ),
            ("6.2 Overtime Calculation Rates", 13, True),
            (
                "Overtime performed by non-exempt staff upon supervisor sign-off is reimbursed at 1.5 times the standard "
                "hourly base rate. Weekend and national holiday shifts accrue compensation at 2.0 times the hourly base rate.",
                11,
                False,
            ),
        ],
        # Page 6: Compensation, Payroll and Bonuses
        [
            ("7. Compensation Structures and Payroll Administration", 16, True),
            (
                "Corporate compensation reflects merit, operational accountability, and market peer benchmarks across each job family.",
                11,
                False,
            ),
            ("7.1 Monthly Remittance Schedule", 13, True),
            (
                "Salary disbursements are remitted via electronic funds transfer on the 25th calendar day of each operating month. "
                "If the 25th coincides with a bank holiday, payment is disbursed on the immediately preceding business day.",
                11,
                False,
            ),
            ("7.2 Annual Merit Incentive Bonuses", 13, True),
            (
                "Discretionary annual bonuses are determined in accordance with organizational EBITDA objectives and individual "
                "performance rating classifications ranging across tiers A (exceptional) through E (unsatisfactory).",
                11,
                False,
            ),
        ],
        # Page 7: Parental, Family Care and Adoption Leave
        [
            ("8. Parental and Family Leave Provisions", 16, True),
            (
                "Allcited supports growing families with paid leave allocations for biological, adoptive, and surrogate parents.",
                11,
                False,
            ),
            ("8.1 Maternity and Primary Caregiver Leave", 13, True),
            (
                "Eligible primary caregivers receive up to 26 consecutive weeks of fully paid maternity leave following birth. "
                "An additional 6 weeks of unpaid leave may be requested subject to department head concurrence.",
                11,
                False,
            ),
            ("8.2 Paternity and Secondary Caregiver Leave", 13, True),
            (
                "Secondary caregivers are eligible for 4 consecutive weeks of fully paid parental leave to be utilized within "
                "the initial 12 months following birth or lawful placement.",
                11,
                False,
            ),
        ],
        # Page 8: Travel, Expenses and Sustenance Ceilings
        [
            ("9. Business Travel and Entertainment Policy", 16, True),
            (
                "All corporate travel must be pre-approved by the cost center vice president prior to commercial booking.",
                11,
                False,
            ),
            ("9.1 Domestic Per Diem Allowances", 13, True),
            (
                "Employees traveling on domestic assignments are entitled to an un-receipted per diem sustenance ceiling of "
                "$75 daily. Hotel lodging allowances are capped at $180 per night before taxes.",
                11,
                False,
            ),
            ("9.2 Private Vehicle Mileage Reimbursement", 13, True),
            (
                "Authorized business transit in personal vehicles is reimbursed at 58 cents per statute mile. Regular commuting "
                "between home and assigned primary office locations is strictly non-reimbursable.",
                11,
                False,
            ),
        ],
        # Page 9: Learning, Tuition and Professional Development
        [
            ("10. Professional Development and Continuing Education", 16, True),
            (
                "The company actively sponsors formal accreditation, engineering licenses, and graduate degree coursework.",
                11,
                False,
            ),
            ("10.1 Tuition Assistance Grants", 13, True),
            (
                "Full-time staff with at least one year of tenure may apply for up to $5,000 per academic year in approved "
                "tuition grants directly relevant to corporate strategic capabilities.",
                11,
                False,
            ),
            ("10.2 Retention Clawback Commitments", 13, True),
            (
                "Tuition grants carry a 12-month retention agreement. Employees leaving voluntarily within 12 months must repay "
                "100% of received funds; those departing between 12 and 24 months repay 50%.",
                11,
                False,
            ),
        ],
        # Page 10: Hardware, Ergonomics and Asset Stewardship
        [
            ("11. Corporate Hardware and Asset Allocations", 16, True),
            (
                "Computing hardware and peripheral equipment are provisioned to meet technical job role specifications.",
                11,
                False,
            ),
            ("11.1 Laptop Provisioning Budgets", 13, True),
            (
                "Engineers and researchers are allocated high-performance workstations with a hardware baseline budget of $2,500. "
                "Equipment refreshes occur on a 36-month standard lifecycle.",
                11,
                False,
            ),
            ("11.2 Home Office Ergonomic Allowance", 13, True),
            (
                "Full-time remote personnel are eligible for a one-time ergonomic stipend of $500 toward certified desk and seating equipment.",
                11,
                False,
            ),
        ],
        # Page 11: Workplace Civility, Equal Opportunity and Anti-Harassment
        [
            ("12. Workplace Civility and Equal Opportunity", 16, True),
            (
                "Allcited enforces strict zero-tolerance policies regarding discrimination, intimidation, and unlawful harassment.",
                11,
                False,
            ),
            ("12.1 Equal Employment Opportunity Mandate", 13, True),
            (
                "Recruitment, compensation, and promotion decisions are conducted purely on qualification, competence, and merit.",
                11,
                False,
            ),
            ("12.2 Grievance Escalation Procedures", 13, True),
            (
                "Personnel experiencing or observing inappropriate conduct may escalate concerns through designated department leads, "
                "the People Operations desk, or the confidential 24/7 ombudsperson channel.",
                11,
                False,
            ),
        ],
        # Page 12: Whistleblower Protection and Compliance Audits
        [
            ("13. Whistleblower Protection and Integrity Oversight", 16, True),
            (
                "Employees are required to promptly report accounting irregularities, safety violations, or regulatory breaches.",
                11,
                False,
            ),
            ("13.1 Non-Retaliation Guarantee", 13, True),
            (
                "The organization strictly guarantees immunity from administrative, disciplinary, or compensation retaliation "
                "for all good-faith whistleblower disclosures.",
                11,
                False,
            ),
            ("13.2 Independent Compliance Helpline", 13, True),
            (
                "Whistleblower complaints can be submitted anonymously through the third-party compliance hotline at 1-800-555-CITE "
                "available 24 hours a day, 365 days a year.",
                11,
                False,
            ),
        ],
        # Page 13: Contractor and Consultant Governance [DISTRACTOR SECTION]
        [
            ("14. External Contractor and Consultant Governance", 16, True),
            (
                "This section outlines terms specifically applicable to third-party consultants and fixed-term contractors.",
                11,
                False,
            ),
            ("14.1 Contractor Notice Requirements (Non-Permanent)", 13, True),
            (
                "Independent contractors and contingent personnel may terminate client engagements with 14 calendar days "
                "written notice (distinguished from permanent staff obligations).",
                11,
                False,
            ),
            ("14.2 Contractor Leave and Payout Ineligibility", 13, True),
            (
                "Contingent workers accrue 10 service credits per contractual quarter but are strictly ineligible for annual leave "
                "encashment, sick leave compensation, or severance settlements.",
                11,
                False,
            ),
            ("14.3 Temporary Credential Lifecycles", 13, True),
            (
                "Contractor accounts and guest network keys expire every 14 days and require bi-weekly project manager re-authorization.",
                11,
                False,
            ),
        ],
        # Page 14: Regional Subsidiary Addendum: UK Operations [DISTRACTOR SECTION]
        [
            ("15. Regional Subsidiary Addendum: United Kingdom", 16, True),
            (
                "Addendum governing personnel engaged by Allcited UK Limited subject to HM Government statutory employment regulations.",
                11,
                False,
            ),
            ("15.1 UK Statutory Annual Leave", 13, True),
            (
                "UK-based personnel are entitled to 28 days of statutory annual holiday including recognized English public holidays.",
                11,
                False,
            ),
            ("15.2 UK Resignation and Probation Notice", 13, True),
            (
                "During probationary engagement, UK personnel may tender notice of 1 calendar month. Following confirmation, "
                "the standard separation notice period of 60 calendar days applies.",
                11,
                False,
            ),
            ("15.3 Sickness Self-Certification", 13, True),
            (
                "UK employees may self-certify illness for up to 7 consecutive days before requiring a doctor fit-note from the NHS.",
                11,
                False,
            ),
        ],
        # Page 15: Corporate Communications and Social Media
        [
            ("16. Corporate Communications and Public Engagements", 16, True),
            (
                "Public statements regarding corporate operations, financial trajectory, or product roadmap require executive sign-off.",
                11,
                False,
            ),
            ("16.1 Media Outreach and Interview Authorizations", 13, True),
            (
                "Only designated executive spokespersons may speak on behalf of Allcited during press or media interviews.",
                11,
                False,
            ),
            ("16.2 Personal Social Media Disclaimers", 13, True),
            (
                "Personnel publishing opinions regarding industry developments must display prominent disclaimers stating that "
                "views expressed are personal and not endorsed by the company.",
                11,
                False,
            ),
        ],
        # Page 16: Comprehensive Procedural and Regulatory Index
        [
            ("17. Regulatory and Procedural Reference Index", 16, True),
            (
                "Master directory cross-referencing internal governance rules and statutory forms cited across handbook chapters:",
                11,
                False,
            ),
            ("Schedule R-1: Rule Cross-References", 13, True),
            (
                "Rule 2.1.4: Carry-forward cap of 8 annual leave days with March 31 expiration date.\n"
                "Rule 2.2.9: Extended critical illness disability pay as stipulated in Medical Schedule MS-4.\n"
                "Rule 63.7.4: Separation leave settlement formula (basic monthly pay / 22 days, 30-day cap).\n"
                "Clause 4.2: Enterprise ISO-27001 password complexity standard and 90-day cycle.\n"
                "Clause 5.1: Private telecommuting workspace and mandatory VPN encapsulation.\n"
                "Procedure EC-101: Conflict of interest declaration protocol to ethics committee.\n"
                "Form HR-702: Medical practitioner certificate for sickness absences exceeding 2 days.",
                10,
                False,
            ),
        ],
    ]

    for page_items in pages_data:
        page = doc.new_page(width=595, height=842)  # A4
        y_cursor = 50.0

        for text, font_size, is_bold in page_items:
            font_name = "helv"  # PyMuPDF standard font
            rect = fitz.Rect(50, y_cursor, 545, y_cursor + 200)

            # Insert text box with wrapping
            page.insert_textbox(
                rect,
                text,
                fontsize=font_size,
                fontname=font_name,
                color=(0, 0, 0),
            )
            # Estimate text height
            lines_est = max(1, len(text) // 75 + 1)
            line_height = font_size * 1.3
            height = lines_est * line_height + 14
            y_cursor += height

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()
    print(f"Created {output_path}")


def create_handbook_docx(output_path: str):
    import docx

    doc = docx.Document()

    doc.add_heading("Allcited Corporate Employee Handbook", level=0)

    # 1. General Employment Framework
    doc.add_heading("1. General Employment Framework", level=1)
    doc.add_paragraph(
        "Welcome to Allcited. This employee handbook sets out the official terms, rules, and conditions "
        "governing all full-time, part-time, and contract personnel across all operating divisions. "
        "Compliance with all company directives and procedural guidelines is mandatory."
    )

    doc.add_heading("1.1 Scope and Application", level=2)
    doc.add_paragraph(
        "This policy applies globally to all employees, consultants, and directors. Specific regional addenda "
        "may provide additional statutory protections where required by municipal labor legislation."
    )

    doc.add_heading("1.2 Code of Business Conduct", level=2)
    doc.add_paragraph(
        "Every team member must act with absolute integrity, transparency, and professional diligence. "
        "Conflicts of interest must be formally declared to the ethics committee under procedure EC-101."
    )

    # 2. Leave and Time-Off Entitlements
    doc.add_heading("2. Leave and Time-Off Entitlements", level=1)
    doc.add_paragraph(
        "The organization provides comprehensive leave arrangements designed to support employee well-being, "
        "rest, health recovery, and family obligations."
    )

    doc.add_heading("2.1 Annual Paid Leave", level=2)
    doc.add_paragraph(
        "Full-time employees accrue 24 days of paid annual leave per calendar year, calculated at the rate "
        "of 2.0 working days for every completed month of active service."
    )

    doc.add_heading("Rule 2.1.4 Carry-Forward Restrictions", level=3)
    doc.add_paragraph(
        "A maximum of 8 unused annual leave days may be carried forward into the subsequent calendar year. "
        "Any surplus beyond 8 days will automatically lapse on March 31 unless granted an executive waiver."
    )

    doc.add_heading("2.2 Sick and Medical Leave", level=2)
    doc.add_paragraph(
        "Staff members are eligible for 12 days of paid sick leave annually. Absences exceeding two consecutive "
        "working days require a medical practitioner certificate submitted via Form HR-702."
    )

    doc.add_heading("Rule 2.2.9 Critical Illness Coverage", level=3)
    doc.add_paragraph(
        "In instances of prolonged hospitalization, employees may draw down extended disability pay as "
        "stipulated in medical schedule MS-4."
    )

    # Table of Leave Entitlements
    table = doc.add_table(rows=1, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Leave Type"
    hdr_cells[1].text = "Annual Entitlement"
    hdr_cells[2].text = "Encashable on Separation"

    rows_data = [
        ("Annual Paid Leave", "24 working days", "Yes (up to 30 days)"),
        ("Sick and Medical Leave", "12 working days", "No"),
        ("Compassionate Leave", "5 days", "No"),
    ]
    for lt, ae, eos in rows_data:
        row_cells = table.add_row().cells
        row_cells[0].text = lt
        row_cells[1].text = ae
        row_cells[2].text = eos

    # 3. Separation, Resignation and Exit Terms
    doc.add_heading("3. Separation, Resignation and Exit Terms", level=1)
    doc.add_paragraph(
        "This section outlines notice periods, property return, and financial settlements upon termination "
        "or voluntary resignation."
    )

    doc.add_heading("3.1 Voluntary Resignation and Notice Period", level=2)
    doc.add_paragraph(
        "Permanent employees who wish to terminate their employment agreement must tender formal written notice "
        "at least 60 calendar days in advance to their designated reporting officer."
    )

    doc.add_heading("3.2 Leave Settlement on Departure", level=2)
    doc.add_paragraph(
        "All accrued but unutilized annual leave will be settled in the final paycheck as per rule 63.7.4. "
        "Employees under active notice may not take paid leave without the written authorization of the Vice President of HR."
    )

    doc.add_heading("3.3 Exit Handover Protocols", level=2)
    doc.add_paragraph(
        "All corporate computing assets, access cards, and confidential proprietary material must be surrendered "
        "to the department supervisor on the final working day."
    )

    # 4. Information Technology and Security
    doc.add_heading("4. Information Technology and Security", level=1)
    doc.add_paragraph(
        "Company-issued electronic devices, networks, credentials, and software are restricted exclusively to authorized "
        "business usage."
    )

    doc.add_heading("Clause 4.2 Security Credential Protocols", level=2)
    doc.add_paragraph(
        "Multi-factor authentication (MFA) is strictly mandatory on all internal systems. Passwords must be at least "
        "16 characters in length and refreshed every 90 days as mandated by standard ISO-27001."
    )

    doc.add_heading("Clause 5.1 Remote Work Policy", level=2)
    doc.add_paragraph(
        "Employees authorized for remote work must maintain a private, secure workspace. Public unsecured Wi-Fi "
        "connections without VPN encapsulation are strictly prohibited."
    )

    # 5. Statutory Schedules and Specialized Rules
    doc.add_heading("5. Statutory Schedules and Specialized Rules", level=1)
    doc.add_heading("Rule 63.7.4 Leave Encashment on Resignation", level=2)
    doc.add_paragraph(
        "Upon voluntary resignation or formal separation, accrued annual leave days up to a cap of 30 working days "
        "shall be encashed at the employee base salary daily rate, computed as monthly basic pay divided by 22 working days. "
        "Sick leave, compassionate leave, and floating holidays are strictly non-encashable and non-transferable."
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(f"Created {output_path}")


def create_sample_deck(output_path: str):
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()

    # Slide 1: Title & Overview
    title_slide_layout = prs.slide_layouts[0]
    slide1 = prs.slides.add_slide(title_slide_layout)
    title1 = slide1.shapes.title
    subtitle1 = slide1.placeholders[1]
    title1.text = "Allcited Corporate Overview"
    subtitle1.text = "Grounded Document Intelligence & Verification Engine"
    slide1.notes_slide.notes_text_frame.text = "Presenter reminder: Emphasize verifiable inline citations [S#]."

    # Slide 2: Security & Protocols
    bullet_slide_layout = prs.slide_layouts[1]
    slide2 = prs.slides.add_slide(bullet_slide_layout)
    title2 = slide2.shapes.title
    title2.text = "Security and ISO-27001 Compliance"
    tf2 = slide2.shapes.placeholders[1].text_frame
    tf2.text = "Multi-factor authentication (MFA) is strictly mandatory across all internal workstations."
    p2 = tf2.add_paragraph()
    p2.text = "Corporate passwords must contain a minimum of 16 characters and refresh every 90 days."
    slide2.notes_slide.notes_text_frame.text = "Mandated under standard ISO-27001 security protocols."

    # Slide 3: Financial Performance (with Table)
    blank_layout = prs.slide_layouts[6]
    slide3 = prs.slides.add_slide(blank_layout)
    tx_box = slide3.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
    tx_box.text_frame.text = "Quarterly Revenue and Growth"

    rows, cols = 5, 3
    left, top, width, height = Inches(1), Inches(1.5), Inches(8), Inches(3)
    table_shape = slide3.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    table.cell(0, 0).text = "Quarter"
    table.cell(0, 1).text = "Revenue ($M)"
    table.cell(0, 2).text = "Growth Rate"

    data = [
        ("Q1 2026", "42.5", "18%"),
        ("Q2 2026", "51.0", "20%"),
        ("Q3 2026", "64.2", "26%"),
        ("Q4 2026", "78.5", "22%"),
    ]
    for r_idx, (q, rev, gr) in enumerate(data, start=1):
        table.cell(r_idx, 0).text = q
        table.cell(r_idx, 1).text = rev
        table.cell(r_idx, 2).text = gr

    # Slide 4: Leave Entitlements
    slide4 = prs.slides.add_slide(bullet_slide_layout)
    slide4.shapes.title.text = "Leave and Time-Off Entitlements"
    tf4 = slide4.shapes.placeholders[1].text_frame
    tf4.text = "Full-time employees accrue 24 days of paid annual leave per calendar year (2.0 days/month)."
    p4_1 = tf4.add_paragraph()
    p4_1.text = "Rule 2.1.4 Carry-Forward Restrictions: Maximum 8 unused annual leave days carried forward."
    p4_2 = tf4.add_paragraph()
    p4_2.text = "Staff members receive 12 days of paid sick leave annually. Absences over 2 days require Form HR-702."
    slide4.notes_slide.notes_text_frame.text = "Accrual rate 2.0 working days per month of service."

    # Slide 5: Separation, Resignation and Exit Terms
    slide5 = prs.slides.add_slide(bullet_slide_layout)
    slide5.shapes.title.text = "Separation, Resignation and Exit Terms"
    tf5 = slide5.shapes.placeholders[1].text_frame
    tf5.text = "Permanent employees must tender formal written notice at least 60 calendar days in advance."
    p5_1 = tf5.add_paragraph()
    p5_1.text = "Rule 63.7.4 Leave Encashment on Resignation: Accrued annual leave capped at 30 working days encashed."
    p5_2 = tf5.add_paragraph()
    p5_2.text = "All computing assets, access cards, and proprietary material surrendered on final day."
    slide5.notes_slide.notes_text_frame.text = "Rule 63.7.4 computed as monthly basic pay divided by 22 working days."

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)
    print(f"Created {output_path}")


def create_sample_spreadsheet(output_path: str):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Department Budgets"

    headers = ["Department", "Headcount", "Annual Budget ($)", "Allocated Spend ($)", "Approval Status"]
    ws.append(headers)

    departments = [
        ("Engineering", 45, 4500000, 4200000, "Approved"),
        ("Legal", 12, 1800000, 1650000, "Approved"),
        ("Security Operations", 8, 1200000, 1150000, "Approved"),
        ("Product Design", 15, 2100000, 1950000, "Approved"),
        ("Customer Success", 25, 2500000, 2300000, "Approved"),
        ("Marketing", 20, 3200000, 3100000, "Approved"),
        ("Finance & Accounting", 10, 1500000, 1400000, "Approved"),
        ("Human Resources", 14, 1600000, 1500000, "Approved"),
        ("Information Technology", 18, 2800000, 2600000, "Approved"),
        ("Research & Development", 30, 5000000, 4800000, "Approved"),
    ]

    # Generate 30 rows total to trigger the 25-row windowing boundary
    for i in range(30):
        dept_name, hc, bud, spend, status = departments[i % len(departments)]
        ws.append([f"{dept_name} Div-{i+1}", hc + i, bud + (i * 10000), spend + (i * 8000), status])

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"Created {output_path}")


def create_scanned_pdf(input_pdf_path: str, output_pdf_path: str):
    """
    Generate a scanned PDF by rasterizing each page into an image
    and re-saving without a digital text layer (<50 chars text), forcing OCR fallback.
    """
    doc = fitz.open(input_pdf_path)
    out_doc = fitz.open()

    # Rasterize first 4 pages to keep OCR evaluation and unit tests fast and focused (covering leave, separation, security)
    for page in list(doc)[:4]:
        pix = page.get_pixmap(dpi=150)
        out_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
        out_page.insert_image(out_page.rect, stream=pix.tobytes("jpeg"))

    Path(output_pdf_path).parent.mkdir(parents=True, exist_ok=True)
    out_doc.save(output_pdf_path, deflate=True, garbage=4)
    out_doc.close()
    doc.close()
    print(f"Created {output_pdf_path}")


if __name__ == "__main__":
    fixtures_dir = Path(__file__).resolve().parent
    create_handbook_pdf(str(fixtures_dir / "handbook.pdf"))
    create_handbook_docx(str(fixtures_dir / "handbook.docx"))
    create_sample_deck(str(fixtures_dir / "presentation.pptx"))
    create_sample_spreadsheet(str(fixtures_dir / "financials.xlsx"))
    create_scanned_pdf(str(fixtures_dir / "handbook.pdf"), str(fixtures_dir / "scanned_handbook.pdf"))
