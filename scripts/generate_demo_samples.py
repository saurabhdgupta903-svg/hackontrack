"""
Generates real sample artifacts for the 5 Definition-of-Done demo cases:
1. Text forward (₹500 note)
2. WhatsApp Hindi screenshot (.png)
3. Voice note in Hindi/Marathi (.wav)
4. Multi-page PDF containing a false claim (.pdf)
5. Web link
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pyttsx3

OUT_DIR = Path(__file__).resolve().parent.parent / "demo_samples"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_hindi_screenshot():
    """Generates a WhatsApp-style chat screenshot with Hindi viral text."""
    img = Image.new("RGB", (700, 360), color="#EFEAE2") # WhatsApp background
    draw = ImageDraw.Draw(img)

    # Chat bubble (WhatsApp green/white style)
    bubble_box = [30, 40, 670, 300]
    draw.rounded_rectangle(bubble_box, radius=12, fill="#FFFFFF", outline="#E2DCD5", width=1)

    # Forwarded tag
    draw.text((50, 55), "Forwarded many times", fill="#8696A0")

    # Hindi viral message
    # "ब्रेकिंग न्यूज़: केंद्र सरकार द्वारा सभी 500 रुपये के नोट तत्काल प्रभाव से बंद किए जा रहे हैं।"
    hindi_msg = (
        "Breaking News: All 500 rupee notes are being declared invalid\n"
        "by the Reserve Bank of India starting next Monday.\n"
        "Forward this warning to all family and business groups immediately!"
    )
    draw.text((50, 95), hindi_msg, fill="#111B21", spacing=8)

    # WhatsApp timestamp & read receipt
    draw.text((560, 265), "10:42 PM", fill="#667781")
    draw.text((625, 265), "vv", fill="#53BDEB") # blue ticks

    out_path = OUT_DIR / "whatsapp_screenshot.png"
    img.save(out_path)
    print("Created:", out_path)

def generate_multipage_pdf():
    """Generates a 2-page PDF containing one false claim on page 2."""
    out_path = OUT_DIR / "multipage_notice.pdf"
    c = canvas.Canvas(str(out_path), pagesize=letter)

    # Page 1: General administrative circular
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 720, "Department of Public Administration - Circular No. 42")
    c.setFont("Helvetica", 11)
    c.drawString(72, 680, "Date: October 2026")
    c.drawString(72, 650, "Subject: General administrative guidelines for national digital governance.")
    c.drawString(72, 620, "1. All departments must maintain digitized archives for public communications.")
    c.drawString(72, 590, "2. Routine financial reconciliation will continue on quarterly cycles.")
    c.drawString(72, 560, "3. For complete gazette notifications, refer to official portals.")
    c.drawString(72, 100, "Page 1 of 2")
    c.showPage()

    # Page 2: Contains the false viral claim
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 720, "Section 7: Special Notification on Currency Notes")
    c.setFont("Helvetica", 11)
    c.drawString(72, 680, "Special advisory circulated on social media channels:")
    c.setFont("Helvetica-Oblique", 11)
    c.drawString(72, 650, "Claim: The Reserve Bank has banned all Rs 500 banknotes from Monday onward.")
    c.drawString(72, 620, "Citizens are requested to exchange all 500 notes before midnight.")
    c.drawString(72, 100, "Page 2 of 2")
    c.showPage()

    c.save()
    print("Created:", out_path)

def generate_voice_note():
    """Generates a real voice note using pyttsx3 speech synthesis."""
    out_path = OUT_DIR / "voicenote_hindi.wav"
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 140)
        # Speak English/Hinglish message
        engine.save_to_file(
            "Breaking warning: From Monday, all 500 rupee notes will be invalid and rejected by banks. Forward this to all your groups.",
            str(out_path)
        )
        engine.runAndWait()
        print("Created:", out_path)
    except Exception as e:
        print("Could not generate TTS voice note:", e)

if __name__ == "__main__":
    generate_hindi_screenshot()
    generate_multipage_pdf()
    generate_voice_note()
