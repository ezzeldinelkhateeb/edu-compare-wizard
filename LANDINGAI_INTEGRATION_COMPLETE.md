# دليل تكامل LandingAI Agentic Document Extraction الشامل
# Complete LandingAI Agentic Document Extraction Integration Guide

## 📋 نظرة عامة / Overview

LandingAI Agentic Document Extraction (ADE) هو نظام ذكي لاستخراج البيانات من المستندات المعقدة بصرياً مثل الجداول والمخططات والنماذج. يتجاوز تقنيات OCR التقليدية بفهم السياق البصري والعلاقات الهيكلية.

### 🌟 الميزات الأساسية / Core Features

1. **Layout-agnostic parsing**: استخراج البيانات من التخطيطات المعقدة بدون قوالب أو تدريب
2. **Element detection**: تحديد العناصر المختلفة (نص، جداول، نماذج، checkboxes)
3. **Hierarchical relationships**: فهم العلاقات الهيكلية بين العناصر
4. **Visual grounding**: توفير إحداثيات دقيقة لكل عنصر مستخرج
5. **Multiple formats**: دعم PDF وصيغ الصور المختلفة
6. **Structured output**: إخراج JSON و Markdown منظم

## 🚀 التثبيت والإعداد / Installation & Setup

### 1. تثبيت المكتبة / Library Installation

```bash
pip install agentic-doc
```

### 2. إعداد API Key

```bash
# Set environment variable
export VISION_AGENT_API_KEY=<your-api-key>

# Or create .env file
echo "VISION_AGENT_API_KEY=<your-api-key>" > .env
```

### 3. متطلبات النظام / System Requirements

- Python 3.9, 3.10, 3.11, or 3.12
- OpenCV-Python (cv2)
- LandingAI API Key

## 📝 استخدام المكتبة / Library Usage

### أساسيات الاستخراج / Basic Extraction

```python
from agentic_doc.parse import parse

# استخراج من ملف محلي / Parse local file
result = parse("path/to/document.pdf")

# الحصول على النتائج / Get results
markdown_content = result[0].markdown
structured_chunks = result[0].chunks

# استخراج من URL
result = parse("https://example.com/document.pdf")
```

### استخراج متعدد الملفات / Multiple Files Processing

```python
from agentic_doc.parse import parse

# معالجة ملفات متعددة / Process multiple files
file_paths = [
    "path/to/document1.pdf",
    "path/to/document2.pdf",
    "path/to/image.png"
]

results = parse(file_paths)

# حفظ النتائج / Save results
results = parse(
    file_paths,
    result_save_dir="path/to/save/results"
)

for result in results:
    print(f"File processed: {result.result_path}")
```

### استخراج البيانات المنظمة / Structured Data Extraction

```python
from pydantic import BaseModel, Field
from agentic_doc.parse import parse

class EducationalContent(BaseModel):
    chapter_title: str = Field(description="عنوان الفصل")
    lesson_objectives: list[str] = Field(description="أهداف الدرس")
    key_concepts: list[str] = Field(description="المفاهيم الأساسية")
    exercises_count: int = Field(description="عدد التمارين")
    difficulty_level: str = Field(description="مستوى الصعوبة")

# استخراج بياني منظم / Structured extraction
results = parse(
    "curriculum_document.pdf",
    extraction_model=EducationalContent
)

extracted_fields = results[0].extraction
print(f"Chapter: {extracted_fields.chapter_title}")
print(f"Objectives: {extracted_fields.lesson_objectives}")
```

### معالجة الملفات الكبيرة / Large Files Processing

```python
from agentic_doc.parse import parse

# معالجة PDF كبير (1000+ صفحة) / Process large PDF
large_pdf_results = parse(
    "large_curriculum.pdf",
    result_save_dir="results/large_processing"
)

# المكتبة تقسم الملف تلقائياً وتعالجه بالتوازي
# Library automatically splits and processes in parallel
```

### حفظ Visual Groundings

```python
from agentic_doc.parse import parse

# حفظ المناطق البصرية المستخرجة / Save visual groundings
results = parse(
    "document.pdf",
    grounding_save_dir="path/to/save/groundings"
)

# الصور ستحفظ في: / Images saved to:
# path/to/save/groundings/document_TIMESTAMP/page_X/CHUNK_TYPE_CHUNK_ID_Y.png

for chunk in results[0].chunks:
    for grounding in chunk.grounding:
        if grounding.image_path:
            print(f"Visual grounding: {grounding.image_path}")
```

### تصور النتائج / Results Visualization

```python
from agentic_doc.parse import parse
from agentic_doc.utils import viz_parsed_document
from agentic_doc.config import VisualizationConfig

# معالجة المستند / Parse document
results = parse("document.pdf")
parsed_doc = results[0]

# إنشاء تصور / Create visualization
images = viz_parsed_document(
    "document.pdf",
    parsed_doc,
    output_dir="visualizations"
)

# تخصيص التصور / Custom visualization
viz_config = VisualizationConfig(
    thickness=2,
    text_bg_opacity=0.8,
    font_scale=0.7,
    color_map={
        ChunkType.TITLE: (0, 0, 255),
        ChunkType.TEXT: (255, 0, 0),
    }
)

custom_images = viz_parsed_document(
    "document.pdf",
    parsed_doc,
    output_dir="custom_visualizations",
    viz_config=viz_config
)
```

## 🔧 إعدادات متقدمة / Advanced Configuration

### ملف .env للإعدادات

```bash
# عدد الملفات المعالجة بالتوازي / Parallel file processing
BATCH_SIZE=4

# عدد الخيوط لكل ملف / Threads per file
MAX_WORKERS=2

# إعدادات إعادة المحاولة / Retry settings
MAX_RETRIES=80
MAX_RETRY_WAIT_TIME=30

# نمط تسجيل إعادة المحاولة / Retry logging style
RETRY_LOGGING_STYLE=log_msg  # Options: log_msg, inline_block, none
```

### إعداد معالجة الأخطاء / Error Handling Setup

```python
from agentic_doc.parse import parse

try:
    results = parse(
        "document.pdf",
        include_marginalia=False,  # استبعاد الهوامش
        include_metadata_in_markdown=False  # استبعاد metadata
    )
    
    # فحص الأخطاء / Check for errors
    for result in results:
        if hasattr(result, 'errors') and result.errors:
            for error in result.errors:
                print(f"Error on page {error.page}: {error.message}")
        
except Exception as e:
    print(f"Processing failed: {e}")
```

## 📊 أنواع البيانات المستخرجة / Extracted Data Types

### JSON Response Structure

```python
{
    "chunks": [
        {
            "chunk_id": "unique_identifier",
            "chunk_type": "text|table|title|form_field|checkbox|image",
            "content": "extracted_content",
            "grounding": [
                {
                    "page": 1,
                    "coordinates": {
                        "x": 100,
                        "y": 150,
                        "width": 200,
                        "height": 50
                    },
                    "image_path": "optional_visual_grounding.png"
                }
            ],
            "metadata": {
                "confidence": 0.95,
                "language": "ar",
                "font_size": 12
            }
        }
    ],
    "markdown": "# Document Content\n\nExtracted text...",
    "extraction": {
        # Structured fields if extraction_model used
    }
}
```

### أنواع العناصر المدعومة / Supported Element Types

1. **TEXT**: النصوص العادية
2. **TITLE**: العناوين والرؤوس  
3. **TABLE**: الجداول والبيانات المنظمة
4. **FORM_FIELD**: حقول النماذج
5. **CHECKBOX**: صناديق الاختيار
6. **IMAGE**: الصور والمخططات
7. **LIST**: القوائم والنقاط
8. **FOOTER**: تذييل الصفحات
9. **HEADER**: رأس الصفحات

## 🔗 Connectors للمصادر المختلفة / Different Source Connectors

### Google Drive Connector

```python
from agentic_doc.parse import parse
from agentic_doc.connectors import GoogleDriveConnectorConfig

config = GoogleDriveConnectorConfig(
    client_secret_file="credentials.json",
    folder_id="google-drive-folder-id"
)

results = parse(config, connector_pattern="*.pdf")
```

### Amazon S3 Connector

```python
from agentic_doc.connectors import S3ConnectorConfig

config = S3ConnectorConfig(
    bucket_name="your-bucket",
    aws_access_key_id="your-key",
    aws_secret_access_key="your-secret",
    region_name="us-east-1"
)

results = parse(config, connector_path="documents/")
```

### Local Directory Connector

```python
from agentic_doc.connectors import LocalConnectorConfig

config = LocalConnectorConfig(recursive=True)
results = parse(
    config,
    connector_path="/path/to/documents",
    connector_pattern="*.pdf"
)
```

### URL Connector

```python
from agentic_doc.connectors import URLConnectorConfig

config = URLConnectorConfig(
    headers={"Authorization": "Bearer token"},
    timeout=60
)

results = parse(config, connector_path="https://example.com/doc.pdf")
```

## 💾 معالجة البيانات الثنائية / Raw Bytes Processing

```python
from agentic_doc.parse import parse

# تحميل ملف كـ bytes / Load file as bytes
with open("document.pdf", "rb") as f:
    raw_bytes = f.read()

# معالجة البيانات الثنائية / Process raw bytes
results = parse(raw_bytes)

# معالجة صورة من bytes / Process image bytes
with open("image.png", "rb") as f:
    image_bytes = f.read()

results = parse(image_bytes)
```

## 🚨 معالجة الأخطاء والحدود / Error Handling & Rate Limits

### Automatic Retry Mechanism

- **Retry Status Codes**: 408, 429, 502, 503, 504
- **Exponential Backoff**: بداية من ثانية واحدة
- **Max Retry Time**: 60 ثانية افتراضياً
- **Jitter**: عشوائية تصل إلى 10 ثوان

### Rate Limits Best Practices

```python
# إعداد للمعالجة عالية الحجم / High-volume processing setup
import os

os.environ["BATCH_SIZE"] = "2"  # تقليل التوازي
os.environ["MAX_WORKERS"] = "3"  # تقليل الخيوط
os.environ["MAX_RETRIES"] = "50"  # زيادة المحاولات
```

## 📈 مقارنة الأداء / Performance Comparison

حسب البحث المرجعي، LandingAI حصل على:
- **Overall Score**: 69/100
- **Node Accuracy**: عالية في استخراج العقد
- **Edge Accuracy**: دقة جيدة في العلاقات
- **Table Extraction**: أداء ممتاز

### مقارنة مع الأدوات الأخرى:
1. **LandingAI**: 69/100 - الأفضل شمولياً
2. **Mistral OCR**: متخصص في RAG
3. **Claude Sonnet 3.7**: استدلال هجين
4. **OpenAI o3-mini**: فعال من حيث التكلفة
5. **Docsumo**: تدريب مخصص

## 💰 التسعير / Pricing

- **LandingAI**: ~$50 per 1M tokens
- **Enterprise Pricing**: متاح للشركات
- **Pay-as-you-go**: حسب الاستخدام

## 🔧 تطبيق في نظام مقارنة المناهج / Curriculum Comparison Implementation

### معالجة ملفات المناهج / Curriculum Files Processing

```python
from agentic_doc.parse import parse
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime

class CurriculumAnalysis(BaseModel):
    subject: str = Field(description="الموضوع أو المادة")
    grade_level: str = Field(description="المستوى الدراسي")
    learning_objectives: list[str] = Field(description="الأهداف التعليمية")
    topics: list[str] = Field(description="المواضيع المغطاة")
    assessment_methods: list[str] = Field(description="طرق التقييم")
    page_count: int = Field(description="عدد الصفحات")
    difficulty_indicators: list[str] = Field(description="مؤشرات الصعوبة")

def process_curriculum_folder(folder_path: str, output_dir: str):
    """معالجة مجلد المناهج وحفظ النتائج"""
    
    # إنشاء مجلد الحفظ
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # معالجة جميع ملفات PDF في المجلد
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    file_paths = [os.path.join(folder_path, f) for f in pdf_files]
    
    # معالجة الملفات مع استخراج منظم
    results = parse(
        file_paths,
        extraction_model=CurriculumAnalysis,
        result_save_dir=f"{output_dir}/raw_extraction_{timestamp}",
        grounding_save_dir=f"{output_dir}/visual_groundings_{timestamp}"
    )
    
    processed_curricula = []
    
    for i, result in enumerate(results):
        curriculum_data = {
            "filename": pdf_files[i],
            "processed_at": timestamp,
            "markdown_content": result.markdown,
            "structured_analysis": result.extraction.dict() if result.extraction else None,
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "type": chunk.chunk_type,
                    "content": chunk.content,
                    "page": chunk.grounding[0].page if chunk.grounding else None,
                    "coordinates": chunk.grounding[0].coordinates if chunk.grounding else None
                }
                for chunk in result.chunks
            ],
            "visual_groundings": [
                grounding.image_path 
                for chunk in result.chunks 
                for grounding in chunk.grounding 
                if grounding.image_path
            ]
        }
        
        processed_curricula.append(curriculum_data)
        
        # حفظ ملف JSON منفصل لكل منهج
        individual_file = f"{output_dir}/curriculum_{i+1}_{timestamp}.json"
        with open(individual_file, 'w', encoding='utf-8') as f:
            json.dump(curriculum_data, f, ensure_ascii=False, indent=2)
    
    # حفظ الملف المجمع
    combined_file = f"{output_dir}/all_curricula_{timestamp}.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(processed_curricula, f, ensure_ascii=False, indent=2)
    
    return processed_curricula

# استخدام الدالة
old_curricula = process_curriculum_folder(
    "uploads/old_curriculum",
    "results/old_curriculum_analysis"
)

new_curricula = process_curriculum_folder(
    "uploads/new_curriculum", 
    "results/new_curriculum_analysis"
)
```

### تحليل مقارن للمناهج / Comparative Curriculum Analysis

```python
def compare_curricula(old_analysis, new_analysis):
    """مقارنة تفصيلية بين المناهج القديمة والجديدة"""
    
    comparison_results = {
        "comparison_timestamp": datetime.now().isoformat(),
        "files_compared": {
            "old": len(old_analysis),
            "new": len(new_analysis)
        },
        "detailed_comparisons": []
    }
    
    for old_curr in old_analysis:
        for new_curr in new_analysis:
            # البحث عن تطابقات محتملة بالموضوع
            if old_curr.get("structured_analysis") and new_curr.get("structured_analysis"):
                old_subject = old_curr["structured_analysis"].get("subject", "")
                new_subject = new_curr["structured_analysis"].get("subject", "")
                
                # مقارنة بسيطة بالنص
                if old_subject.lower() in new_subject.lower() or new_subject.lower() in old_subject.lower():
                    comparison = {
                        "old_file": old_curr["filename"],
                        "new_file": new_curr["filename"],
                        "subject_match": f"{old_subject} -> {new_subject}",
                        "changes": {
                            "learning_objectives": {
                                "old": old_curr["structured_analysis"].get("learning_objectives", []),
                                "new": new_curr["structured_analysis"].get("learning_objectives", []),
                                "added": [],
                                "removed": [],
                                "common": []
                            },
                            "topics": {
                                "old": old_curr["structured_analysis"].get("topics", []),
                                "new": new_curr["structured_analysis"].get("topics", []),
                                "added": [],
                                "removed": [],
                                "common": []
                            }
                        },
                        "content_similarity": len(set(old_curr["markdown_content"].split()) & 
                                                 set(new_curr["markdown_content"].split())) / 
                                               max(len(old_curr["markdown_content"].split()), 
                                                   len(new_curr["markdown_content"].split())),
                        "visual_elements": {
                            "old_groundings_count": len(old_curr.get("visual_groundings", [])),
                            "new_groundings_count": len(new_curr.get("visual_groundings", []))
                        }
                    }
                    
                    # تحليل التغييرات في الأهداف
                    old_objectives = set(old_curr["structured_analysis"].get("learning_objectives", []))
                    new_objectives = set(new_curr["structured_analysis"].get("learning_objectives", []))
                    
                    comparison["changes"]["learning_objectives"]["added"] = list(new_objectives - old_objectives)
                    comparison["changes"]["learning_objectives"]["removed"] = list(old_objectives - new_objectives)
                    comparison["changes"]["learning_objectives"]["common"] = list(old_objectives & new_objectives)
                    
                    # تحليل التغييرات في المواضيع
                    old_topics = set(old_curr["structured_analysis"].get("topics", []))
                    new_topics = set(new_curr["structured_analysis"].get("topics", []))
                    
                    comparison["changes"]["topics"]["added"] = list(new_topics - old_topics)
                    comparison["changes"]["topics"]["removed"] = list(old_topics - new_topics)
                    comparison["changes"]["topics"]["common"] = list(old_topics & new_topics)
                    
                    comparison_results["detailed_comparisons"].append(comparison)
    
    return comparison_results
```

## 📋 قائمة مراجعة التطبيق / Implementation Checklist

### ✅ خطوات التطبيق الأساسية

1. **تثبيت المكتبة**
   ```bash
   pip install agentic-doc
   ```

2. **إعداد API Key**
   ```bash
   export VISION_AGENT_API_KEY=your_key_here
   ```

3. **اختبار الاتصال**
   ```python
   from agentic_doc.parse import parse
   result = parse("test_document.pdf")
   ```

4. **إعداد معالجة الأخطاء**
5. **تخصيص الإعدادات حسب الحاجة**
6. **تطبيق الاستخراج المنظم**
7. **حفظ Visual Groundings**
8. **تطبيق المقارنة الذكية**

### 🔧 متطلبات التطوير

1. **Backend Integration**
   - FastAPI endpoints للمعالجة
   - Celery tasks للمعالجة غير المتزامنة
   - Database models للنتائج
   - WebSocket للتحديثات المباشرة

2. **Frontend Integration**
   - Progress tracking للمعالجة
   - Results visualization
   - File management interface
   - Comparison viewer

3. **Testing & Validation**
   - Unit tests للوظائف الأساسية
   - Integration tests للـ API
   - Performance benchmarks
   - Error handling validation

## 🎯 الخلاصة / Summary

LandingAI Agentic Document Extraction يوفر:
- **دقة عالية** في استخراج البيانات المعقدة
- **مرونة كبيرة** في التعامل مع أنواع مختلفة من المستندات
- **تكامل سهل** مع الأنظمة الموجودة
- **معالجة متوازية** للملفات الكبيرة
- **إخراج منظم** جاهز للاستخدام في تطبيقات الذكاء الاصطناعي

هذا النظام مثالي لمقارنة المناهج التعليمية حيث يمكنه:
- استخراج المحتوى التعليمي بدقة
- تحديد العناصر البصرية والجداول
- توفير إحداثيات دقيقة لكل عنصر
- حفظ النتائج بصيغ متعددة (JSON, Markdown)
- معالجة مجلدات كاملة من المستندات

---

**ملاحظة**: هذا الدليل يغطي جميع الجوانب التقنية لتطبيق LandingAI في نظام مقارنة المناهج. للحصول على أفضل النتائج، يُنصح بتجربة الإعدادات المختلفة واختبار المكتبة مع عينات من المستندات المستهدفة. 