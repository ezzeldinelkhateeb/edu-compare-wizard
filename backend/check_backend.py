"""
فحص واستكمال الوحدات المفقودة للباك ايند
Check and Complete Missing Backend Modules
"""
import os
import sys
from pathlib import Path

# إضافة مجلد الباك ايند للـ path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

def check_imports():
    """فحص جميع الاستيرادات المطلوبة"""
    print("🔍 فحص الوحدات المطلوبة...")
    
    missing_modules = []
    working_modules = []
    
    # قائمة الوحدات الأساسية
    required_modules = [
        ("loguru", "للتسجيل"),
        ("pydantic", "للبيانات المنظمة"),
        ("google.generativeai", "خدمة Gemini"),
        ("PIL", "معالجة الصور"),
        ("numpy", "العمليات الرياضية"),
        ("opencv-python", "معالجة الصور المتقدمة"),
        ("scikit-image", "خوارزميات الصور"),
        ("imagehash", "بصمة الصور"),
        ("requests", "طلبات HTTP"),
        ("aiofiles", "معالجة الملفات غير المتزامنة"),
        ("asyncio", "البرمجة غير المتزامنة"),
        ("json", "تحليل JSON"),
        ("difflib", "مقارنة النصوص"),
    ]
    
    for module_name, description in required_modules:
        try:
            if module_name == "opencv-python":
                import cv2
                working_modules.append((module_name, description, cv2.__version__))
            elif module_name == "PIL":
                from PIL import Image
                working_modules.append((module_name, description, Image.__version__))
            elif module_name == "google.generativeai":
                import google.generativeai as genai
                working_modules.append((module_name, description, "✓"))
            elif module_name == "scikit-image":
                import skimage
                working_modules.append((module_name, description, skimage.__version__))
            else:
                exec(f"import {module_name}")
                # محاولة الحصول على الإصدار
                try:
                    version = eval(f"{module_name}.__version__")
                except:
                    version = "✓"
                working_modules.append((module_name, description, version))
        except ImportError as e:
            missing_modules.append((module_name, description, str(e)))
    
    # طباعة النتائج
    print(f"\n✅ الوحدات المتوفرة ({len(working_modules)}):")
    for module, desc, version in working_modules:
        print(f"   ✓ {module} ({desc}) - {version}")
    
    if missing_modules:
        print(f"\n❌ الوحدات المفقودة ({len(missing_modules)}):")
        for module, desc, error in missing_modules:
            print(f"   ✗ {module} ({desc}) - {error}")
        
        print(f"\n📦 لتثبيت الوحدات المفقودة:")
        install_commands = {
            "loguru": "pip install loguru",
            "pydantic": "pip install pydantic",
            "google.generativeai": "pip install google-generativeai",
            "PIL": "pip install Pillow",
            "numpy": "pip install numpy",
            "opencv-python": "pip install opencv-python",
            "scikit-image": "pip install scikit-image",
            "imagehash": "pip install ImageHash",
            "requests": "pip install requests",
            "aiofiles": "pip install aiofiles",
        }
        
        for module, _, _ in missing_modules:
            if module in install_commands:
                print(f"   {install_commands[module]}")
    
    return len(missing_modules) == 0

def check_service_files():
    """فحص ملفات الخدمات"""
    print("\n🔍 فحص ملفات الخدمات...")
    
    required_files = [
        "app/services/__init__.py",
        "app/services/gemini_service.py", 
        "app/services/landing_ai_service.py",
        "app/services/visual_comparison_service.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/__init__.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = backend_path / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            existing_files.append((file_path, size))
        else:
            missing_files.append(file_path)
    
    print(f"\n✅ الملفات الموجودة ({len(existing_files)}):")
    for file_path, size in existing_files:
        print(f"   ✓ {file_path} ({size} bytes)")
    
    if missing_files:
        print(f"\n❌ الملفات المفقودة ({len(missing_files)}):")
        for file_path in missing_files:
            print(f"   ✗ {file_path}")
    
    return len(missing_files) == 0

def create_missing_config():
    """إنشاء ملف التكوين إذا كان مفقوداً"""
    config_dir = backend_path / "app" / "core"
    config_file = config_dir / "config.py"
    
    if not config_file.exists():
        print("📝 إنشاء ملف التكوين المفقود...")
        
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_content = '''"""
إعدادات التطبيق
Application Configuration
"""
import os
from typing import Dict, Any

class Settings:
    """إعدادات التطبيق"""
    
    def __init__(self):
        # إعدادات Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.gemini_temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
        
        # إعدادات LandingAI
        self.vision_agent_api_key = os.getenv("VISION_AGENT_API_KEY", "")
        self.landingai_batch_size = int(os.getenv("LANDINGAI_BATCH_SIZE", "4"))
        
        # إعدادات عامة
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # إعدادات المعالجة
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "50")) # MB
        self.supported_formats = ["pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"]

def get_settings() -> Settings:
    """الحصول على إعدادات التطبيق"""
    return Settings()
'''
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ تم إنشاء {config_file}")
        return True
    
    return False

def create_missing_init_files():
    """إنشاء ملفات __init__.py المفقودة"""
    init_files = [
        "app/__init__.py",
        "app/core/__init__.py",
        "app/services/__init__.py"
    ]
    
    created_files = []
    
    for init_file in init_files:
        full_path = backend_path / init_file
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if "services" in init_file:
                content = '# Services package init\n'
            elif "core" in init_file:
                content = '# Core package init\n'
            else:
                content = '# App package init\n'
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(init_file)
    
    if created_files:
        print(f"📝 تم إنشاء ملفات __init__.py:")
        for file_path in created_files:
            print(f"   ✓ {file_path}")
    
    return len(created_files)

def main():
    """الدالة الرئيسية للفحص"""
    print("🔧 فحص واستكمال الباك ايند")
    print("=" * 50)
    
    # فحص الوحدات
    modules_ok = check_imports()
    
    # فحص الملفات
    files_ok = check_service_files()
    
    # إنشاء الملفات المفقودة
    created_config = create_missing_config()
    created_inits = create_missing_init_files()
    
    print(f"\n📊 تقرير الفحص:")
    print(f"   📦 الوحدات: {'✅ متوفرة' if modules_ok else '❌ ناقصة'}")
    print(f"   📁 الملفات: {'✅ متوفرة' if files_ok else '❌ ناقصة'}")
    
    if created_config or created_inits > 0:
        print(f"   🔧 تم إنشاء ملفات مفقودة: {created_inits + (1 if created_config else 0)}")
    
    print(f"\n{'✅ الباك ايند جاهز للاختبار!' if modules_ok and files_ok else '⚠️ يحتاج الباك ايند إلى إصلاحات'}")
    
    if modules_ok and files_ok:
        print("\n🚀 يمكنك الآن تشغيل:")
        print("   python test_all_services.py")
    
    return 0 if modules_ok and files_ok else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"💥 خطأ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
