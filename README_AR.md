# ID MOHAMED SALAH — نسخة ويب تجريبية

## تشغيل على الكمبيوتر
1. ثبّت Python 3.10 أو 3.11 أو 3.12.
2. فك ضغط المشروع.
3. افتح الطرفية داخل مجلد المشروع وشغّل:
   ```bash
   python -m venv .venv
   ```
   Windows:
   ```bash
   .venv\Scripts\activate
   ```
   macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```
4. ثبّت المكتبات:
   ```bash
   pip install -r requirements.txt
   ```
5. شغّل:
   ```bash
   streamlit run app.py
   ```
6. افتح الرابط المحلي الذي يظهر في الطرفية. لفتحها من الهاتف على نفس شبكة Wi-Fi شغّل:
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```
   ثم افتح عنوان الكمبيوتر المحلي مع المنفذ `8501` من الهاتف.

## نشرها على الويب
ارفع الملفات `app.py` و`requirements.txt` إلى مستودع GitHub، ثم أنشئ تطبيقًا في Streamlit Community Cloud واختر `app.py`.
قد يتطلب تنزيل نماذج OCR مساحة ووقتًا ملحوظين في أول تشغيل.

## ما تم اختباره
- فحص صياغة Python.
- اختبارات منطقية لفك الرقم القومي والتحقق من التاريخ.
- إنشاء ملف Excel من جدول تجريبي.
لم يتم الادعاء بأن OCR نجح على بطاقات حقيقية؛ يجب اختبار الصور محليًا ومراجعة النتائج.
