"""BhumiLekh Demo Data & Synthetic Document Generator.

Generates:
1. `data/sample_dataset/sample_land_records.json` (Structured multi-state ground-truth land records)
2. `data/synthetic_documents/` (Scanned synthetic images & PDFs in Marathi, Hindi, Tamil, Telugu, Kannada, Gujarati, Bengali, and English)
3. `data/synthetic_documents/cadastral_village_fmb_map.png` (Cadastral parcel map for vectorization)
"""
import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample_dataset"
SYNTH_DIR = DATA_DIR / "synthetic_documents"

SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
SYNTH_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Structured Ground-Truth Dataset (sample_land_records.json)
# ---------------------------------------------------------------------------
SAMPLE_RECORDS = [
    {
        "id": "REC-MH-712-001",
        "state": "Maharashtra",
        "document_type": "7/12 (Satbara)",
        "language": "mr",
        "script": "Devanagari",
        "entities": {
            "village": "शिवाजीनगर",
            "tehsil": "हवेली",
            "district": "पुणे",
            "survey_number": "245/1A",
            "khata_number": "45",
            "owner_name": "रमेश कुमार शर्मा",
            "area": 1.45,
            "area_unit": "हेक्टर",
            "land_type": "जिरायत"
        },
        "text": "महाराष्ट्र शासन - महसूल विभाग\nगाव नमुना ७/१२ (अधिकार अभिलेख पत्रक)\nगाव: शिवाजीनगर, तालुका: हवेली, जिल्हा: पुणे\nभूमापन क्रमांक / सर्व्हे क्र.: 245/1A\nखाते क्रमांक: 45\nभोगवटादाराचे नाव: रमेश कुमार शर्मा\nएकूण क्षेत्र: 1.45 हेक्टर\nआकारणी: 4.50 रु."
    },
    {
        "id": "REC-UP-KHATAUNI-002",
        "state": "Uttar Pradesh",
        "document_type": "खतौनी (Khatauni)",
        "language": "hi",
        "script": "Devanagari",
        "entities": {
            "village": "बख्शी का तालाब",
            "tehsil": "बख्शी का तालाब",
            "district": "लखनऊ",
            "khasra_number": "142",
            "khata_number": "88",
            "owner_name": "राम प्रसाद वर्मा",
            "area": 0.854,
            "area_unit": "हेक्टेयर",
            "land_type": "कृषि"
        },
        "text": "उत्तर प्रदेश भू-अभिलेख खतौनी (अधिकार अभिलेख)\nग्राम: बख्शी का तालाब, परगना व तहसील: बख्शी का तालाब, जनपद: लखनऊ\nखाता संख्या: 88, फसली वर्ष: 1428-1433\nखसरा संख्या: 142\nखातेदार का नाम: राम प्रसाद वर्मा\nपिता का नाम: सुंदर लाल वर्मा\nक्षेत्रफल: 0.854 हेक्टेयर"
    },
    {
        "id": "REC-TN-PATTA-003",
        "state": "Tamil Nadu",
        "document_type": "பட்டா / சிட்டா (Patta Chitta)",
        "language": "ta",
        "script": "Tamil",
        "entities": {
            "village": "மேலூர்",
            "tehsil": "மேலூர்",
            "district": "மதுரை",
            "survey_number": "88/2A",
            "patta_number": "450",
            "owner_name": "முத்துசாமி கவுண்டர்",
            "area": 1.12,
            "area_unit": "ஹெக்டேர்"
        },
        "text": "தமிழ்நாடு அரசு - வருவாய்த்துறை\nபட்டா / சிட்டா சான்று\nமாவட்டம்: மதுரை, வட்டம்: மேலூர், கிராமம்: மேலூர்\nபட்டா எண்: 450\nஉரிமையாளர் பெயர்: முத்துசாமி கவுண்டர்\nபுல எண் / உட்பிரிவு: 88/2A\nவிஸ்தீரணம்: 1.12 ஹெக்டேர்"
    },
    {
        "id": "REC-KA-RTC-004",
        "state": "Karnataka",
        "document_type": "ಭೂಮಿ RTC / ಪಹಣಿ",
        "language": "kn",
        "script": "Kannada",
        "entities": {
            "village": "ದೇವನಹಳ್ಳಿ",
            "tehsil": "ದೇವನಹಳ್ಳಿ",
            "district": "ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ",
            "survey_number": "72/1",
            "hissa_number": "1",
            "owner_name": "ನಾರಾಯಣ ಸ್ವಾಮಿ",
            "area": 2.34,
            "area_unit": "ಎಕರೆ"
        },
        "text": "ಕರ್ನಾಟಕ ಸರ್ಕಾರ - ಕಂದಾಯ ಇಲಾಖೆ\nಭೂಮಿ ಆರ್.ಟಿ.ಸಿ (ಪಹಣಿ)\nಜಿಲ್ಲೆ: ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ, ತಾಲೂಕು: ದೇವನಹಳ್ಳಿ, ಗ್ರಾಮ: ದೇವನಹಳ್ಳಿ\nಸರ್ವೆ ನಂ: 72/1, ಹಿಸ್ಸಾ ನಂ: 1\nಖಾತೆದಾರರ ಹೆಸರು: ನಾರಾಯಣ ಸ್ವಾಮಿ\nವಿಸ್ತೀರ್ಣ: 2.34 ಎಕರೆ"
    },
    {
        "id": "REC-TS-ADANGAL-005",
        "state": "Telangana",
        "document_type": "పహాణీ / అడంగల్ (Adangal)",
        "language": "te",
        "script": "Telugu",
        "entities": {
            "village": "షాద్‌నగర్",
            "tehsil": "షాద్‌నగర్",
            "district": "రంగారెడ్డి",
            "survey_number": "104/A",
            "khata_number": "512",
            "owner_name": "వెంకటేశ్వర్లు రెడ్డి",
            "area": 3.25,
            "area_unit": "ఎకరాలు"
        },
        "text": "తెలంగాణ ప్రభుత్వం - రెవెన్యూ శాఖ\nపహాణీ / రికార్డ్ ఆఫ్ రైట్స్ (ROR)\nజిల్లా: రంగారెడ్డి, మండలం: షాద్‌నగర్, గ్రామం: షాద్‌నగర్\nసర్వే నంబర్: 104/A, ఖాతా నంబరు: 512\nపట్టాదారు పేరు: వెంకటేశ్వర్లు రెడ్డి\nవిస్తీర్ణం: 3.25 ఎకరాలు"
    },
    {
        "id": "REC-GJ-ANYROR-006",
        "state": "Gujarat",
        "document_type": "AnyRoR 7/12",
        "language": "gu",
        "script": "Gujarati",
        "entities": {
            "village": "સાનંદ",
            "tehsil": "સાનંદ",
            "district": "અમદાવાદ",
            "survey_number": "315/2",
            "khata_number": "120",
            "owner_name": "પટેલ હરેશભાઈ",
            "area": 1.80,
            "area_unit": "હેક્ટર"
        },
        "text": "ગુજરાત સરકાર - મહેસૂલ વિભાગ\nAnyRoR ગામ નમૂના નં. ૭/૧૨\nજિલ્લો: અમદાવાદ, તાલુકો: સાનંદ, ગામ: સાનંદ\nસર્વે નંબર: 315/2, ખાતા નંબર: 120\nખાતેદારનું નામ: પટેલ હરેશભાઈ\nક્ષેત્રફળ: 1.80 હેક્ટર"
    },
    {
        "id": "REC-WB-ROR-007",
        "state": "West Bengal",
        "document_type": "বাংলারভূমি খতিয়ান (Banglarbhumi RoR)",
        "language": "bn",
        "script": "Bengali",
        "entities": {
            "village": "বারুইপুর",
            "tehsil": "বারুইপুর",
            "district": "দক্ষিণ ২৪ পরগনা",
            "plot_number": "520",
            "khatian_number": "304",
            "owner_name": "অমিত কুমার ঘোষ",
            "area": 0.45,
            "area_unit": "একর"
        },
        "text": "পশ্চিমবঙ্গ সরকার - ভূমি ও ভূমি সংস্কার দপ্তর\nবাংলারভূমি খতিয়ান তথ্য (RoR)\nজেলা: দক্ষিণ ২৪ পরগনা, ব্লক: বারুইপুর, মৌজা: বারুইপুর\nখতিয়ান নম্বর: 304, দাগ নম্বর: 520\nরায়তের নাম: অমিত কুমার ঘোষ\nজমির পরিমাণ: 0.45 একর"
    },
    {
        "id": "REC-EN-DEED-008",
        "state": "Karnataka",
        "document_type": "Sale Deed / Land Title",
        "language": "en",
        "script": "Latin",
        "entities": {
            "village": "Whitefield",
            "tehsil": "KR Puram",
            "district": "Bengaluru Urban",
            "survey_number": "108/3",
            "plot_number": "12B",
            "owner_name": "Vikram Malhotra",
            "registration_number": "REG-BLR-2024-8891",
            "area": 2400.0,
            "area_unit": "sq_ft"
        },
        "text": "GOVERNMENT OF KARNATAKA - DEPARTMENT OF STAMPS AND REGISTRATION\nABSOLUTE SALE DEED\nRegistration No: REG-BLR-2024-8891\nDistrict: Bengaluru Urban, Taluk: KR Puram, Village: Whitefield\nSurvey Number: 108/3, Plot Number: 12B\nPurchaser / Owner Name: Vikram Malhotra\nExtent / Measurement: 2400 sq.ft\nBoundaries: North - Road, South - Plot 12A, East - Survey 108/4, West - Main Road"
    }
]

# Write sample_land_records.json
with open(SAMPLE_DIR / "sample_land_records.json", "w", encoding="utf-8") as f:
    json.dump(SAMPLE_RECORDS, f, ensure_ascii=False, indent=2)
print("Saved data/sample_dataset/sample_land_records.json")


# ---------------------------------------------------------------------------
# 2. Render Synthetic Scanned Document Images & PDFs
# ---------------------------------------------------------------------------
def get_font_for_script(script: str, size: int = 22):
    font_map = {
        "Devanagari": "/System/Library/Fonts/Kohinoor.ttc",
        "Tamil": "/System/Library/Fonts/Supplemental/Tamil Sangam MN.ttc",
        "Kannada": "/System/Library/Fonts/Supplemental/Kannada Sangam MN.ttc",
        "Telugu": "/System/Library/Fonts/KohinoorTelugu.ttc",
        "Gujarati": "/System/Library/Fonts/KohinoorGujarati.ttc",
        "Bengali": "/System/Library/Fonts/KohinoorBangla.ttc",
        "Latin": "/System/Library/Fonts/Supplemental/Arial.ttf",
    }
    font_path = font_map.get(script, "/System/Library/Fonts/Supplemental/Arial.ttf")
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


def render_document(record: dict, output_base: str):
    script = record["script"]
    title_font = get_font_for_script(script, 26)
    body_font = get_font_for_script(script, 20)
    label_font = get_font_for_script(script, 18)

    # Document canvas: 900x1200
    img = Image.new("RGB", (900, 1200), color=(252, 250, 242))
    draw = ImageDraw.Draw(img)

    # Scanned document outer double borders
    draw.rectangle([(25, 25), (875, 1175)], outline=(70, 70, 70), width=3)
    draw.rectangle([(32, 32), (868, 1168)], outline=(140, 140, 140), width=1)

    # Header Box
    draw.rectangle([(45, 45), (855, 140)], fill=(240, 238, 228), outline=(100, 100, 100), width=2)
    draw.text((60, 55), record["state"].upper() + " - " + record["document_type"], font=title_font, fill=(20, 20, 20))
    draw.text((60, 95), f"Official Revenue Record • ID: {record['id']}", font=label_font, fill=(80, 80, 80))

    # Details Table
    draw.rectangle([(45, 160), (855, 820)], outline=(100, 100, 100), width=2)
    # Horizontal grid lines
    y_offsets = [230, 300, 370, 440, 510, 580, 650, 720]
    for y in y_offsets:
        draw.line([(45, y), (855, y)], fill=(180, 180, 180), width=1)
    # Vertical grid line
    draw.line([(320, 160), (320, 820)], fill=(180, 180, 180), width=2)

    # Table content
    rows = [
        ("Village / ग्राम / ஊர்", record["entities"].get("village", "-")),
        ("Tehsil / Taluk / வட்டம்", record["entities"].get("tehsil", "-")),
        ("District / जिल्हा / மாவட்டம்", record["entities"].get("district", "-")),
        ("Survey / Khasra / புல எண்", str(record["entities"].get("survey_number") or record["entities"].get("khasra_number") or record["entities"].get("plot_number") or "-")),
        ("Khata / Patta / ఖాతా సంఖ్య", str(record["entities"].get("khata_number") or record["entities"].get("patta_number") or record["entities"].get("khatian_number") or "-")),
        ("Owner Name / खातेदार / பட்டாதார்", record["entities"].get("owner_name", "-")),
        ("Area / क्षेत्र / விஸ்தீரணம்", f"{record['entities'].get('area', '-')} {record['entities'].get('area_unit', '')}"),
        ("Classification / Land Type", record["entities"].get("land_type", "Agriculture / बागायत")),
    ]

    for idx, (lbl, val) in enumerate(rows):
        y_pos = 180 + idx * 70
        draw.text((60, y_pos), lbl, font=label_font, fill=(70, 70, 70))
        draw.text((340, y_pos), str(val), font=body_font, fill=(10, 10, 10))

    # Raw Text section below table
    draw.rectangle([(45, 840), (855, 1060)], fill=(248, 246, 238), outline=(160, 160, 160), width=1)
    draw.text((55, 850), "TRANSCRIPTION / अभिलेख सारांश:", font=label_font, fill=(60, 60, 60))
    
    text_lines = record["text"].split("\n")
    for l_idx, line in enumerate(text_lines[:7]):
        draw.text((55, 885 + l_idx * 24), line, font=label_font, fill=(30, 30, 30))

    # Stamp / Signature Box
    draw.rectangle([(620, 1080), (840, 1150)], outline=(120, 60, 60), width=2)
    draw.text((630, 1090), "OFFICIAL SEAL", font=label_font, fill=(150, 40, 40))
    draw.text((630, 1120), "Tahsildar / Dy. Collector", font=label_font, fill=(80, 80, 80))

    # Save PNG and PDF
    png_path = SYNTH_DIR / f"{output_base}.png"
    pdf_path = SYNTH_DIR / f"{output_base}.pdf"
    img.save(png_path)
    img.save(pdf_path, "PDF", resolution=150.0)
    print(f"Generated {png_path.name} & {pdf_path.name}")


# Render each document
file_bases = {
    "REC-MH-712-001": "maharashtra_satbara_7_12",
    "REC-UP-KHATAUNI-002": "up_khatauni_khasra",
    "REC-TN-PATTA-003": "tamilnadu_patta_chitta",
    "REC-KA-RTC-004": "karnataka_bhoomi_rtc",
    "REC-TS-ADANGAL-005": "telangana_adangal",
    "REC-GJ-ANYROR-006": "gujarat_anyror_7_12",
    "REC-WB-ROR-007": "bengali_banglarbhumi_ror",
    "REC-EN-DEED-008": "english_sale_deed",
}

for rec in SAMPLE_RECORDS:
    base_name = file_bases.get(rec["id"])
    if base_name:
        render_document(rec, base_name)


# ---------------------------------------------------------------------------
# 3. Render Cadastral Map (FMB / Village Map) for GIS Vectorization
# ---------------------------------------------------------------------------
def render_cadastral_map():
    map_img = Image.new("RGB", (1000, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(map_img)
    latin_font = get_font_for_script("Latin", 24)
    title_font = get_font_for_script("Latin", 30)

    # Outer border
    draw.rectangle([(20, 20), (980, 780)], outline=(0, 0, 0), width=4)
    draw.text((50, 35), "FIELD MEASUREMENT BOOK (FMB) / CADASTRAL SKETCH", font=title_font, fill=(0, 0, 0))
    draw.text((50, 75), "Village: Melur, Taluk: Melur, District: Madurai • Scale 1:1000", font=latin_font, fill=(100, 100, 100))

    # Draw 4 parcels
    # Parcel 101
    draw.polygon([(60, 130), (450, 130), (450, 420), (60, 420)], outline=(0, 0, 0), width=3)
    draw.text((220, 260), "101/1", font=title_font, fill=(0, 0, 0))

    # Parcel 102
    draw.polygon([(470, 130), (940, 130), (940, 420), (470, 420)], outline=(0, 0, 0), width=3)
    draw.text((680, 260), "102", font=title_font, fill=(0, 0, 0))

    # Parcel 103
    draw.polygon([(60, 450), (450, 450), (350, 740), (60, 740)], outline=(0, 0, 0), width=3)
    draw.text((180, 580), "103/A", font=title_font, fill=(0, 0, 0))

    # Parcel 104
    draw.polygon([(470, 450), (940, 450), (940, 740), (370, 740)], outline=(0, 0, 0), width=3)
    draw.text((650, 580), "104", font=title_font, fill=(0, 0, 0))

    map_path = SYNTH_DIR / "cadastral_village_fmb_map.png"
    map_img.save(map_path)
    print(f"Generated {map_path.name}")

render_cadastral_map()
print("Synthetic demo data generation completed successfully!")
