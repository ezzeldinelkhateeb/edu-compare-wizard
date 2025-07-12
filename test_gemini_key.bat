@echo off
echo 🧪 اختبار مفتاح Gemini API الجديد
echo =========================================
echo 🔑 Key: AIzaSyB-2F7RdbLi3BMUb2ixF07cGS0OFnq910U
echo =========================================

cd backend
set GEMINI_API_KEY=AIzaSyB-2F7RdbLi3BMUb2ixF07cGS0OFnq910U

echo 🔄 اختبار الاتصال...
python test_gemini_simple.py

echo.
echo =========================================
pause 