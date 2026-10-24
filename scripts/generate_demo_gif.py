"""
Generate assets/demo.gif demonstrating Allcited's interactive document Q&A workflow:
Upload -> Chunk Indexing -> Question -> Pipeline Stages -> Cited Streaming Answer -> Source Receipt Inspection.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 720, 420
BG_COLOR = (15, 17, 23)          # Slate dark
CARD_BG = (24, 27, 36)           # Card dark
ACCENT_BLUE = (59, 130, 246)     # Primary blue
ACCENT_GREEN = (34, 197, 94)     # Success green
TEXT_MAIN = (243, 244, 246)      # White-gray
TEXT_MUTED = (156, 163, 175)     # Muted gray
BORDER_COLOR = (45, 52, 68)      # Border
CHIP_BG = (37, 45, 62)           # Citation chip


def create_base_canvas(title: str = "ALLCITED · Document Q&A with Receipts") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, WIDTH, 48], fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((24, 16), title, fill=TEXT_MAIN)
    draw.text((WIDTH - 140, 16), "MODE: CLOUD", fill=ACCENT_BLUE)

    return img, draw


def generate_frames() -> list[Image.Image]:
    frames = []

    # Frame 1: Empty state with dropzone
    img, draw = create_base_canvas()
    draw.rounded_rectangle([40, 70, WIDTH - 40, 200], radius=8, outline=BORDER_COLOR, fill=CARD_BG, width=2)
    draw.text((WIDTH // 2 - 130, 110), "Drop handbook or policy document here", fill=TEXT_MUTED)
    draw.text((WIDTH // 2 - 110, 140), "Supports PDF, DOCX, PPTX, XLSX, HTML, URL", fill=(100, 116, 139))
    draw.rounded_rectangle([WIDTH // 2 - 60, 165, WIDTH // 2 + 60, 190], radius=4, fill=ACCENT_BLUE)
    draw.text((WIDTH // 2 - 42, 170), "Upload File", fill=(255, 255, 255))
    frames.append(img)

    # Frame 2: Upload in progress
    img, draw = create_base_canvas()
    draw.rounded_rectangle([40, 70, WIDTH - 40, 200], radius=8, outline=ACCENT_BLUE, fill=CARD_BG, width=2)
    draw.text((60, 95), "Uploading corporate_handbook.pdf (1.2 MB)...", fill=TEXT_MAIN)
    draw.rectangle([60, 130, WIDTH - 60, 140], fill=(40, 48, 64))
    draw.rectangle([60, 130, WIDTH - 200, 140], fill=ACCENT_BLUE)
    draw.text((60, 155), "Extracting sections & tables · OCR fallback standby...", fill=TEXT_MUTED)
    frames.append(img)

    # Frame 3: Indexing ready
    img, draw = create_base_canvas()
    draw.rounded_rectangle([40, 70, WIDTH - 40, 140], radius=8, outline=BORDER_COLOR, fill=CARD_BG)
    draw.text((60, 85), "corporate_handbook.pdf", fill=TEXT_MAIN)
    draw.text((60, 110), "READY · 42 chunks indexed · 12 pages · FAISS + BM25 cached", fill=ACCENT_GREEN)

    # Suggested question
    draw.rounded_rectangle([40, 160, WIDTH - 40, 210], radius=6, outline=BORDER_COLOR, fill=CARD_BG)
    draw.text((60, 175), "Q: What is the international remote work stipend limit?", fill=TEXT_MUTED)
    frames.append(img)

    # Frame 4: Pipeline search & routing
    img, draw = create_base_canvas()
    draw.rounded_rectangle([40, 70, WIDTH - 40, 120], radius=6, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((60, 85), "corporate_handbook.pdf (Ready)", fill=ACCENT_GREEN)

    # Pipeline progress chip
    draw.rounded_rectangle([40, 135, WIDTH - 40, 170], radius=4, fill=(30, 38, 54), outline=ACCENT_BLUE)
    draw.text((55, 145), "ROUTE: lookup  |  RETRIEVE: 25 chunks (BM25+Dense)  |  RERANK: top 4 kept", fill=ACCENT_BLUE)

    # User message
    draw.rounded_rectangle([180, 185, WIDTH - 40, 225], radius=6, fill=(35, 45, 65))
    draw.text((200, 195), "What is the international remote work stipend limit?", fill=TEXT_MAIN)
    frames.append(img)

    # Frame 5: Streaming grounded answer with citations
    img, draw = create_base_canvas()
    # User message
    draw.rounded_rectangle([180, 65, WIDTH - 40, 105], radius=6, fill=(35, 45, 65))
    draw.text((200, 75), "What is the international remote work stipend limit?", fill=TEXT_MAIN)

    # Assistant card
    draw.rounded_rectangle([40, 120, WIDTH - 40, 270], radius=8, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((60, 135), "Under Section 4.2 (Remote Work Provisions), eligible full-time", fill=TEXT_MAIN)
    draw.text((60, 155), "employees may receive an annual international stipend of up to $1,500", fill=TEXT_MAIN)

    # Citation Chip S1
    draw.rounded_rectangle([520, 152, 570, 172], radius=4, fill=ACCENT_BLUE)
    draw.text((530, 155), "[S1]", fill=(255, 255, 255))

    draw.text((60, 180), "This reimbursement requires prior Manager Approval pursuant to", fill=TEXT_MAIN)
    draw.text((60, 200), "Rule 63.7.4", fill=TEXT_MAIN)

    # Citation Chip S2 (2nd-hop)
    draw.rounded_rectangle([140, 197, 235, 217], radius=4, fill=(147, 51, 234))
    draw.text((148, 200), "[S2 (2nd-hop)]", fill=(255, 255, 255))

    draw.text((245, 200), "before travel booking.", fill=TEXT_MAIN)

    # Verified grounded badge
    draw.rounded_rectangle([60, 235, 220, 258], radius=4, fill=(20, 50, 35))
    draw.text((70, 240), "Grounded in 2 verified sources", fill=ACCENT_GREEN)
    frames.append(img)

    # Frame 6: Citation Inspection / Source Receipt Panel Open
    img, draw = create_base_canvas()
    # Left split: chat
    draw.rounded_rectangle([20, 65, 380, 380], radius=6, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((35, 80), "Answer (Grounded)", fill=TEXT_MUTED)
    draw.text((35, 110), "Stipend limit: $1,500/year [S1]", fill=TEXT_MAIN)
    draw.text((35, 135), "Condition: Rule 63.7.4 approval [S2]", fill=TEXT_MAIN)

    # Right split: Source Receipt Inspector
    draw.rounded_rectangle([400, 65, WIDTH - 20, 380], radius=6, fill=(20, 24, 34), outline=ACCENT_BLUE, width=2)
    draw.text((415, 80), "SOURCE RECEIPT: [S1]", fill=ACCENT_BLUE)
    draw.text((415, 105), "Document: corporate_handbook.pdf", fill=TEXT_MUTED)
    draw.text((415, 125), "Section: 4. Benefits > 4.2 Remote Work", fill=TEXT_MUTED)
    draw.text((415, 145), "Page: 14  |  Score: 0.94  |  Vector+BM25 RRF", fill=TEXT_MUTED)

    # Highlighted quote
    draw.rounded_rectangle([415, 175, WIDTH - 35, 280], radius=4, fill=(32, 42, 60), outline=(50, 70, 105))
    draw.text((425, 190), '"Employees authorized for international', fill=TEXT_MAIN)
    draw.text((425, 210), 'remote operations shall receive an', fill=TEXT_MAIN)
    draw.text((425, 230), 'annual allowance capped at $1,500 USD', fill=ACCENT_GREEN)
    draw.text((425, 250), 'for connectivity and workspace expenses."', fill=TEXT_MAIN)

    draw.rounded_rectangle([415, 305, 550, 330], radius=4, fill=CARD_BG, outline=BORDER_COLOR)
    draw.text((425, 312), "Decision Trail: OK", fill=ACCENT_GREEN)
    frames.append(img)

    return frames


def main():
    frames = generate_frames()
    # Durations in ms: frame 1 (1500), 2 (1500), 3 (1800), 4 (1800), 5 (2500), 6 (3500)
    durations = [1500, 1500, 1800, 1800, 2500, 3500]

    gif_path = ASSETS_DIR / "demo.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"Generated animated demo GIF at: {gif_path} ({gif_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
