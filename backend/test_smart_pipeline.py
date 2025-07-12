#!/usr/bin/env python3
"""
اختبار سريع للنظام الذكي المطور
Quick test for the enhanced smart system
"""

import sys
from pathlib import Path

# إضافة مسار المشروع للاستيراد
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.smart_batch_processor import SmartBatchProcessor

def test_smart_pipeline():
    """اختبار سريع للنظام الذكي"""
    
    print("🧪 اختبار النظام الذكي للمقارنة")
    print("="*50)
    
    try:
        # إعداد المعالج
        processor = SmartBatchProcessor(
            old_dir="../test/2024",
            new_dir="../test/2025",
            max_workers=2,  # عدد أقل لتجنب الخطأ
            visual_threshold=0.95
        )
        
        # تشغيل المعالجة
        processor.run_batch_processing()
        
        print("\n✅ تم الاختبار بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_smart_pipeline() 