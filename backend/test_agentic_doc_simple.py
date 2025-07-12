from agentic_doc.parse import parse
import os

api_key = os.environ.get("VISION_AGENT_API_KEY")
if not api_key:
    print("❌ متغير البيئة VISION_AGENT_API_KEY غير مضبوط!")
    exit(1)

file_path = r"D:\ezz\compair\edu-compare-wizard\backend\103.jpg"

try:
    result = parse(file_path)
    print("\n===== Markdown Extracted Data =====\n")
    print(result[0].markdown)
    print("\n===== JSON Chunks =====\n")
    print(result[0].chunks)
    if hasattr(result[0], 'result_path'):
        print(f"\nResult JSON saved at: {result[0].result_path}")
except Exception as e:
    print(f"❌ حدث خطأ أثناء تحليل الملف: {e}")