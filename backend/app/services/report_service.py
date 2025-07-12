"""
خدمة إنتاج التقارير بصيغة Markdown و HTML
Enhanced Report Generation Service for Markdown and HTML
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from jinja2 import Template
from markdown import markdown
from pydantic import BaseModel, Field
from loguru import logger

from app.core.config import get_settings

settings = get_settings()


class ReportData(BaseModel):
    """بيانات التقرير"""
    session_id: str
    old_image_name: str
    new_image_name: str
    old_extracted_text: str
    new_extracted_text: str
    visual_similarity: float
    text_analysis: Dict[str, Any]
    processing_time: Dict[str, float]
    confidence_scores: Dict[str, float]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class EnhancedReportService:
    """خدمة إنتاج التقارير المحسنة"""
    
    def __init__(self):
        self.output_dir = os.path.join(settings.UPLOAD_DIR, "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # قوالب التقارير
        self.markdown_template = self._create_markdown_template()
        self.html_template = self._create_html_template()
        
        logger.info("✅ تم تكوين خدمة التقارير المحسنة")
    
    async def generate_comprehensive_report(
        self,
        session_id: str,
        report_data: ReportData,
        include_extracted_text: bool = True,
        include_visual_analysis: bool = True
    ) -> Dict[str, str]:
        """
        إنتاج تقرير شامل بصيغة MD و HTML
        Generate comprehensive report in MD and HTML formats
        """
        logger.info(f"📋 إنشاء تقرير شامل للجلسة: {session_id}")
        
        try:
            # إنشاء مجلد التقرير
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = os.path.join(self.output_dir, f"report_{session_id}_{timestamp}")
            os.makedirs(report_dir, exist_ok=True)
            
            # إنتاج تقرير Markdown
            md_content = await self._generate_markdown_report(
                report_data, include_extracted_text, include_visual_analysis
            )
            md_path = os.path.join(report_dir, f"تقرير_المقارنة_{session_id}.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # إنتاج تقرير HTML
            html_content = await self._generate_html_report(
                report_data, include_extracted_text, include_visual_analysis
            )
            html_path = os.path.join(report_dir, f"تقرير_المقارنة_{session_id}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # إنشاء تقرير النصوص المستخرجة منفصل
            if include_extracted_text:
                extracted_text_md = self._generate_extracted_text_report(report_data)
                extracted_path = os.path.join(report_dir, f"النصوص_المستخرجة_{session_id}.md")
                with open(extracted_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text_md)
            
            logger.info(f"✅ تم إنتاج التقرير الشامل: {report_dir}")
            
            return {
                "markdown_path": md_path,
                "html_path": html_path,
                "extracted_text_path": extracted_path if include_extracted_text else None,
                "report_directory": report_dir
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنتاج التقرير: {e}")
            raise
    
    async def _generate_markdown_report(
        self,
        data: ReportData,
        include_extracted_text: bool,
        include_visual_analysis: bool
    ) -> str:
        """إنتاج تقرير Markdown"""
        
        # تحضير البيانات للقالب
        template_data = {
            "session_id": data.session_id,
            "timestamp": datetime.fromisoformat(data.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "old_image": data.old_image_name,
            "new_image": data.new_image_name,
            "visual_similarity": data.visual_similarity,
            "text_analysis": data.text_analysis,
            "processing_time": data.processing_time,
            "confidence_scores": data.confidence_scores,
            "include_extracted_text": include_extracted_text,
            "include_visual_analysis": include_visual_analysis,
            "old_text": data.old_extracted_text if include_extracted_text else "",
            "new_text": data.new_extracted_text if include_extracted_text else "",
            "new_questions": data.text_analysis.get("new_questions", []),
            "new_explanations": data.text_analysis.get("new_explanations", []),
            "has_significant_changes": data.text_analysis.get("has_significant_changes", False)
        }
        
        template = Template(self.markdown_template)
        return template.render(**template_data)
    
    async def _generate_html_report(
        self,
        data: ReportData,
        include_extracted_text: bool,
        include_visual_analysis: bool
    ) -> str:
        """إنتاج تقرير HTML"""
        
        # تحضير البيانات للقالب
        template_data = {
            "session_id": data.session_id,
            "timestamp": datetime.fromisoformat(data.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "old_image": data.old_image_name,
            "new_image": data.new_image_name,
            "visual_similarity": data.visual_similarity,
            "text_analysis": data.text_analysis,
            "processing_time": data.processing_time,
            "confidence_scores": data.confidence_scores,
            "include_visual_analysis": include_visual_analysis,
            "new_questions": data.text_analysis.get("new_questions", []),
            "new_explanations": data.text_analysis.get("new_explanations", []),
            "major_differences": data.text_analysis.get("major_differences", []),
            "has_significant_changes": data.text_analysis.get("has_significant_changes", False),
            "summary": data.text_analysis.get("summary", ""),
            "recommendation": data.text_analysis.get("recommendation", "")
        }
        
        template = Template(self.html_template)
        return template.render(**template_data)
    
    def _generate_extracted_text_report(self, data: ReportData) -> str:
        """إنتاج تقرير النصوص المستخرجة"""
        
        return f"""# النصوص المستخرجة - جلسة {data.session_id}

**تاريخ المعالجة:** {datetime.fromisoformat(data.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

---

## النص المستخرج من الصورة القديمة
**اسم الملف:** {data.old_image_name}
**مستوى الثقة:** {data.confidence_scores.get('old_confidence', 0):.1%}

```
{data.old_extracted_text}
```

---

## النص المستخرج من الصورة الجديدة
**اسم الملف:** {data.new_image_name}
**مستوى الثقة:** {data.confidence_scores.get('new_confidence', 0):.1%}

```
{data.new_extracted_text}
```

---

## إحصائيات المعالجة
- **وقت استخراج النص القديم:** {data.processing_time.get('old_ocr', 0):.2f} ثانية
- **وقت استخراج النص الجديد:** {data.processing_time.get('new_ocr', 0):.2f} ثانية
- **وقت تحليل المقارنة:** {data.processing_time.get('comparison', 0):.2f} ثانية
- **الوقت الإجمالي:** {sum(data.processing_time.values()):.2f} ثانية

---

## ملاحظات
- تم استخراج النصوص باستخدام تقنيات OCR متقدمة
- النصوص قد تحتاج إلى مراجعة يدوية لضمان الدقة الكاملة
- مستوى الثقة يعكس جودة الاستخراج التلقائي
"""
    
    def _create_markdown_template(self) -> str:
        """إنشاء قالب Markdown"""
        
        return """# تقرير مقارنة المناهج التعليمية

**معرف الجلسة:** {{ session_id }}  
**تاريخ المعالجة:** {{ timestamp }}

---

## ملخص المقارنة

| العنصر | القيمة |
|---------|--------|
| الصورة القديمة | {{ old_image }} |
| الصورة الجديدة | {{ new_image }} |
| نسبة التشابه البصري | {{ "%.1f"|format(visual_similarity) }}% |
| نسبة التشابه النصي | {{ "%.1f"|format(text_analysis.similarity_percentage) }}% |
| التغييرات الجوهرية | {{ "نعم" if has_significant_changes else "لا" }} |

---

{% if new_questions %}
## الأسئلة الجديدة 🆕

{% for question in new_questions %}
{{ loop.index }}. {{ question }}
{% endfor %}

---
{% endif %}

{% if new_explanations %}
## الشروحات الجديدة 📚

{% for explanation in new_explanations %}
{{ loop.index }}. {{ explanation }}
{% endfor %}

---
{% endif %}

## تحليل المقارنة

### الملخص
{{ text_analysis.summary }}

### التوصيات
{{ text_analysis.recommendation }}

{% if text_analysis.major_differences %}
### الاختلافات الجوهرية
{% for diff in text_analysis.major_differences %}
- {{ diff }}
{% endfor %}
{% endif %}

---

## إحصائيات المعالجة

| المرحلة | الوقت (ثانية) |
|----------|---------------|
| استخراج النص القديم | {{ "%.2f"|format(processing_time.get('old_ocr', 0)) }} |
| استخراج النص الجديد | {{ "%.2f"|format(processing_time.get('new_ocr', 0)) }} |
| تحليل المقارنة | {{ "%.2f"|format(processing_time.get('comparison', 0)) }} |
| **الإجمالي** | **{{ "%.2f"|format(processing_time.values()|sum) }}** |

---

{% if include_extracted_text %}
## النصوص المستخرجة

### النص القديم
```
{{ old_text }}
```

### النص الجديد
```
{{ new_text }}
```
{% endif %}

---

*تم إنتاج هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية*
"""
    
    def _create_html_template(self) -> str:
        """إنشاء قالب HTML"""
        
        return """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير مقارنة المناهج التعليمية</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 1.2em;
        }
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        .new-content {
            background-color: #e8f5e8;
            border-right: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .new-content h3 {
            color: #28a745;
            margin-top: 0;
        }
        .differences {
            background-color: #fff3cd;
            border-right: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .differences h3 {
            color: #856404;
            margin-top: 0;
        }
        .list-item {
            background-color: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-radius: 5px;
            border-right: 3px solid #007bff;
        }
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .stats-table th,
        .stats-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: center;
        }
        .stats-table th {
            background-color: #007bff;
            color: white;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }
        .highlight {
            background-color: #fff3cd;
            padding: 2px 5px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 تقرير مقارنة المناهج التعليمية</h1>
            <p><strong>معرف الجلسة:</strong> {{ session_id }}</p>
            <p><strong>تاريخ المعالجة:</strong> {{ timestamp }}</p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>التشابه البصري</h3>
                <div class="value">{{ "%.1f"|format(visual_similarity) }}%</div>
            </div>
            <div class="summary-card">
                <h3>التشابه النصي</h3>
                <div class="value">{{ "%.1f"|format(text_analysis.similarity_percentage) }}%</div>
            </div>
            <div class="summary-card">
                <h3>التغييرات الجوهرية</h3>
                <div class="value">{{ "نعم" if has_significant_changes else "لا" }}</div>
            </div>
        </div>

        {% if new_questions %}
        <div class="new-content">
            <h3>🆕 الأسئلة الجديدة</h3>
            {% for question in new_questions %}
            <div class="list-item">
                <strong>{{ loop.index }}.</strong> {{ question }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if new_explanations %}
        <div class="new-content">
            <h3>📚 الشروحات الجديدة</h3>
            {% for explanation in new_explanations %}
            <div class="list-item">
                <strong>{{ loop.index }}.</strong> {{ explanation }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if major_differences %}
        <div class="differences">
            <h3>⚠️ الاختلافات الجوهرية</h3>
            {% for diff in major_differences %}
            <div class="list-item">
                • {{ diff }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <h2>📊 تحليل المقارنة</h2>
        
        <h3>الملخص</h3>
        <p>{{ summary }}</p>
        
        <h3>التوصيات</h3>
        <p class="highlight">{{ recommendation }}</p>

        <h2>⏱️ إحصائيات المعالجة</h2>
        <table class="stats-table">
            <thead>
                <tr>
                    <th>المرحلة</th>
                    <th>الوقت (ثانية)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>استخراج النص القديم</td>
                    <td>{{ "%.2f"|format(processing_time.get('old_ocr', 0)) }}</td>
                </tr>
                <tr>
                    <td>استخراج النص الجديد</td>
                    <td>{{ "%.2f"|format(processing_time.get('new_ocr', 0)) }}</td>
                </tr>
                <tr>
                    <td>تحليل المقارنة</td>
                    <td>{{ "%.2f"|format(processing_time.get('comparison', 0)) }}</td>
                </tr>
                <tr style="background-color: #e9ecef; font-weight: bold;">
                    <td>الإجمالي</td>
                    <td>{{ "%.2f"|format(processing_time.values()|sum) }}</td>
                </tr>
            </tbody>
        </table>

        <div class="footer">
            <p><em>تم إنتاج هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية</em></p>
        </div>
    </div>
</body>
</html>"""

    async def health_check(self) -> Dict[str, Any]:
        """فحص صحة الخدمة"""
        return {
            "service": "EnhancedReportService",
            "status": "healthy",
            "output_directory": self.output_dir,
            "templates": {
                "markdown": "loaded",
                "html": "loaded"
            }
        } 