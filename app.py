import io
import re
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

st.set_page_config(page_title="ID MOHAMED SALAH", page_icon="🪪", layout="wide")

GOVERNORATES = {
    "01": "القاهرة", "02": "الإسكندرية", "03": "بورسعيد", "04": "السويس",
    "11": "دمياط", "12": "الدقهلية", "13": "الشرقية", "14": "القليوبية",
    "15": "كفر الشيخ", "16": "الغربية", "17": "المنوفية", "18": "البحيرة",
    "19": "الإسماعيلية", "21": "الجيزة", "22": "بني سويف", "23": "الفيوم",
    "24": "المنيا", "25": "أسيوط", "26": "سوهاج", "27": "قنا",
    "28": "أسوان", "29": "الأقصر", "31": "البحر الأحمر", "32": "الوادي الجديد",
    "33": "مطروح", "34": "شمال سيناء", "35": "جنوب سيناء", "88": "خارج مصر"
}

def western_digits(s):
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    return str(s).translate(trans)

def decode_national_id(raw):
    digits = re.sub(r"\D", "", western_digits(raw))
    if len(digits) != 14 or digits[0] not in "23":
        return "", "", "", "يجب أن يتكون الرقم القومي من 14 رقمًا ويبدأ بـ 2 أو 3."
    try:
        year = (1900 if digits[0] == "2" else 2000) + int(digits[1:3])
        month, day = int(digits[3:5]), int(digits[5:7])
        born = date(year, month, day).isoformat()
        gov = GOVERNORATES.get(digits[7:9], "كود محافظة غير معروف")
        gender = "ذكر" if int(digits[12]) % 2 else "أنثى"
        return born, gov, gender, ""
    except ValueError:
        return "", "", "", "تاريخ الميلاد داخل الرقم القومي غير صحيح."

@st.cache_resource(show_spinner=False)
def get_reader():
    import easyocr
    return easyocr.Reader(["ar", "en"], gpu=False, verbose=False)

def read_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")
    # modest contrast/sharpening can help OCR, without modifying the stored original
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = img.filter(ImageFilter.SHARPEN)
    reader = get_reader()
    lines = reader.readtext(__import__("numpy").array(img), detail=0, paragraph=False)
    return img, [str(x).strip() for x in lines if str(x).strip()]

def extract_record(filename, image_bytes):
    record = {
        "اسم الملف": filename, "الاسم الكامل": "", "العنوان": "",
        "الرقم القومي": "", "تاريخ الميلاد": "", "المحافظة": "", "النوع": "",
        "حالة المراجعة": "تحتاج مراجعة", "نص OCR الكامل": ""
    }
    try:
        _, lines = read_image(image_bytes)
        text = "\n".join(lines)
        # Search all OCR text for 14 digits, accepting Arabic-Indic digits and separators.
        normalized = western_digits(text)
        candidates = re.findall(r"(?<!\d)(?:\d[\s\-]*){14}(?!\d)", normalized)
        nid = re.sub(r"\D", "", candidates[0]) if candidates else ""
        record["الرقم القومي"] = nid
        born, gov, gender, error = decode_national_id(nid)
        record["تاريخ الميلاد"], record["المحافظة"], record["النوع"] = born, gov, gender
        # Conservative heuristics only: OCR does not reliably identify field positions in every photo.
        # Keep text available and make every field editable for human review.
        usable = [re.sub(r"\s+", " ", x).strip() for x in lines]
        non_numeric = [x for x in usable if len(re.sub(r"\W", "", x)) >= 3 and not re.fullmatch(r"[\d\s\-]+", x)]
        if non_numeric:
            record["الاسم الكامل"] = non_numeric[0]
        if len(non_numeric) > 1:
            record["العنوان"] = non_numeric[-1]
        record["نص OCR الكامل"] = text
        if error:
            record["حالة المراجعة"] = "مراجعة الرقم القومي"
        elif not record["الاسم الكامل"] or not record["العنوان"]:
            record["حالة المراجعة"] = "مراجعة الاسم والعنوان"
        else:
            record["حالة المراجعة"] = "تم الاستخراج - يلزم التأكيد"
    except Exception as e:
        record["حالة المراجعة"] = "تعذر تشغيل OCR: " + str(e)[:180]
    return record

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="بيانات البطاقات")
        ws = writer.sheets["بيانات البطاقات"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            width = min(max(max(len(str(c.value or "")) for c in col) + 2, 14), 45)
            ws.column_dimensions[col[0].column_letter].width = width
    out.seek(0)
    return out.getvalue()

st.markdown("""
<style>
.block-container {max-width: 1150px; padding-top: 1.2rem; padding-bottom: 2rem}
.hero {padding: 1.2rem; border-radius: 16px; background: linear-gradient(120deg,#102a43,#176b87); color: white}
.hero h1 {color:white; margin:0}
.small-note {font-size:.92rem; color:#666}
div[data-testid="stFileUploader"] {border-radius: 12px}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🪪 ID MOHAMED SALAH</h1><p>استخراج تجريبي لبيانات بطاقات الرقم القومي المصرية ومراجعتها وتصديرها إلى Excel</p></div>', unsafe_allow_html=True)
st.warning("الخصوصية: صور البطاقات والبيانات الشخصية حساسة. استخدم نسخة محلية أو استضافة موثوقة، ولا ترفع بيانات حقيقية لخدمة عامة دون موافقة وضوابط حماية مناسبة.")
st.info("محرك OCR حقيقي (EasyOCR)؛ قد يحتاج تنزيل نماذج في أول تشغيل. الاسم والعنوان المستخرجان آليًا تقديريان ويجب مراجعتهما يدويًا. لا تعتبر النتائج إثباتًا للهوية.")

with st.expander("طريقة الاستخدام", expanded=True):
    st.markdown("1. ارفع صورة واحدة أو عدة صور واضحة للوجه الذي يحتوي على البيانات.\n2. اضغط **ابدأ استخراج البيانات** وانتظر انتهاء المعالجة.\n3. راجع وعدّل الخانات في الجدول؛ ترتيب الاسم والعنوان الآلي غير مضمون.\n4. اضغط **تنزيل Excel** لحفظ النتائج.")

uploads = st.file_uploader("ارفع صور البطاقات", type=["png","jpg","jpeg","webp","bmp","tif","tiff"], accept_multiple_files=True)
if "records" not in st.session_state:
    st.session_state.records = []

col1, col2 = st.columns([1, 1])
with col1:
    run = st.button("🔍 ابدأ استخراج البيانات", type="primary", use_container_width=True, disabled=not uploads)
with col2:
    if st.button("مسح النتائج من الجلسة", use_container_width=True):
        st.session_state.records = []
        st.rerun()

if run and uploads:
    new_records = []
    progress = st.progress(0, text="جارٍ تجهيز الصور...")
    for i, uploaded in enumerate(uploads):
        with st.spinner(f"معالجة الصورة {i+1} من {len(uploads)}: {uploaded.name}"):
            new_records.append(extract_record(uploaded.name, uploaded.getvalue()))
        progress.progress((i+1)/len(uploads), text=f"تمت معالجة {i+1} من {len(uploads)}")
    st.session_state.records = new_records
    progress.empty()
    st.success(f"انتهت محاولة معالجة {len(new_records)} صورة. راجع النتائج قبل التصدير.")

if st.session_state.records:
    st.subheader("مراجعة البيانات")
    df = pd.DataFrame(st.session_state.records)
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "نص OCR الكامل": st.column_config.TextColumn("نص OCR الكامل", width="large"),
            "حالة المراجعة": st.column_config.TextColumn("حالة المراجعة", width="medium"),
            "الرقم القومي": st.column_config.TextColumn("الرقم القومي", help="تأكد من 14 رقمًا")
        }, key="review_editor")
    st.session_state.records = edited.to_dict("records")
    st.download_button("⬇️ تنزيل ملف Excel", data=to_excel(edited),
        file_name="ID_MOHAMED_SALAH.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary", use_container_width=True)
    st.caption("لا يتم تصحيح الاسم أو العنوان تلقائيًا على نحو مضمون. راجع كل صف قبل استخدامه.")

with st.expander("معلومات عن المحرك والحدود"):
    st.markdown("- يتعرف EasyOCR على النصوص من الصورة، لكنه لا يضمن تحديد الاسم والعنوان بدقة لأن مواضع الحقول تختلف باختلاف جودة الصورة والقص والانعكاس.\n- تاريخ الميلاد والنوع والمحافظة تُستنتج من بنية الرقم القومي فقط بعد التحقق من شكله وتاريخ الميلاد.\n- البيانات تبقى في جلسة التطبيق الحالية، ولا تحفظ هذه النسخة تلقائيًا في قاعدة بيانات دائمة.\n- لا توجد خدمة OCR سحابية مدفوعة؛ أول تشغيل يحتاج الإنترنت لتنزيل نماذج EasyOCR، وبعد تنزيلها يمكن تشغيله محليًا دون إرسال الصور إلى خدمة OCR خارجية.")
