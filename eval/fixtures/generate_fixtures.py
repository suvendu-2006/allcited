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


if __name__ == "__main__":
    create_handbook_pdf("eval/fixtures/handbook.pdf")
    create_handbook_docx("eval/fixtures/handbook.docx")
