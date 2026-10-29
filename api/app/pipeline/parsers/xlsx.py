import io
from typing import List, Union

import openpyxl

from app.pipeline.parsers.base import ParsedBlock

ROW_WINDOW_SIZE = 25


class XLSXParserError(Exception):
    """Raised when XLSX spreadsheet cannot be read or parsed."""

    pass


def parse_xlsx(
    content: Union[str, bytes],
    source_name: str = "spreadsheet.xlsx",
) -> List[ParsedBlock]:
    """
    Parse an Excel (.xlsx) workbook into structured ParsedBlocks.
    For each sheet, rows are batched into 25-row windows formatted as Markdown tables,
    preserving headers, numeric values, and formulas.
    """
    if isinstance(content, str):
        with open(content, "rb") as f:
            bytes_data = f.read()
    else:
        bytes_data = content

    try:
        wb = openpyxl.load_workbook(io.BytesIO(bytes_data), data_only=False, read_only=True)
    except Exception as e:
        raise XLSXParserError(f"Corrupt or unreadable XLSX document: {str(e)}") from e

    try:
        blocks: List[ParsedBlock] = []

        for sheet_idx, sheet_name in enumerate(wb.sheetnames, start=1):
            ws = wb[sheet_name]
            all_rows: List[List[str]] = []

            try:
                for row in ws.iter_rows(values_only=True):
                    # Filter trailing None values but preserve interior Nones as empty string
                    row_str = [str(cell).strip() if cell is not None else "" for cell in row]
                    if any(row_str):
                        all_rows.append(row_str)
            except Exception:
                # Sheet iteration fallback
                continue

            if not all_rows:
                continue

            headers = all_rows[0]
            max_cols = max(len(headers), max((len(r) for r in all_rows), default=0))
            headers = headers + [""] * (max_cols - len(headers))

            data_rows = all_rows[1:]
            if not data_rows:
                # Single row sheet (header only)
                table_md = (
                    "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * max_cols) + " |"
                )
                blocks.append(
                    ParsedBlock(
                        text=table_md,
                        section_path=[sheet_name],
                        page=sheet_idx,
                        source=source_name,
                    )
                )
                continue

            # Chunk into windows of ROW_WINDOW_SIZE rows
            for win_idx in range(0, len(data_rows), ROW_WINDOW_SIZE):
                window_slice = data_rows[win_idx : win_idx + ROW_WINDOW_SIZE]

                lines = []
                lines.append("| " + " | ".join(headers) + " |")
                lines.append("| " + " | ".join(["---"] * max_cols) + " |")

                for r in window_slice:
                    padded = r + [""] * (max_cols - len(r))
                    clean_cells = [c.replace("\n", " ").replace("|", "\\|") for c in padded]
                    lines.append("| " + " | ".join(clean_cells) + " |")

                table_md = "\n".join(lines)
                start_row = win_idx + 2  # 1-based, after header
                end_row = min(win_idx + 1 + len(window_slice), len(data_rows) + 1)
                window_label = f"{sheet_name} (Rows {start_row}–{end_row})"

                blocks.append(
                    ParsedBlock(
                        text=table_md,
                        section_path=[sheet_name, window_label],
                        page=sheet_idx,
                        source=source_name,
                    )
                )

        return blocks
    finally:
        wb.close()
