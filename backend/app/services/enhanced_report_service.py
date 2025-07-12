"""
خدمة إنتاج التقارير بصيغة Markdown و HTML
Enhanced Report Generation Service for Markdown and HTML
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
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
        logger.info("✅ تم تكوين خدمة التقارير المحسنة")
    
    async def generate_comprehensive_report(
        self,
        session_id: str,
        report_data: ReportData,
        include_extracted_text: bool = True,
        include_visual_analysis: bool = True
    ) -> Dict[str, str]:
        """إنتاج تقرير شامل بصيغة MD و HTML"""
        logger.info(f"📋 إنشاء تقرير شامل للجلسة: {session_id}")
        
        try:
            # إنشاء مجلد التقرير
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = os.path.join(self.output_dir, f"report_{session_id}_{timestamp}")
            os.makedirs(report_dir, exist_ok=True)
            
            # إنتاج تقرير Markdown
            md_content = self._generate_markdown_report(report_data, include_extracted_text)
            md_path = os.path.join(report_dir, f"تقرير_المقارنة_{session_id}.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # إنتاج تقرير HTML
            html_content = self._generate_html_report(report_data, include_visual_analysis)
            html_path = os.path.join(report_dir, f"تقرير_المقارنة_{session_id}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # إنشاء تقرير النصوص المستخرجة منفصل
            extracted_path = None
            if include_extracted_text:
                extracted_text_md = self._generate_extracted_text_report(report_data)
                extracted_path = os.path.join(report_dir, f"النصوص_المستخرجة_{session_id}.md")
                with open(extracted_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text_md)
            
            logger.info(f"✅ تم إنتاج التقرير الشامل: {report_dir}")
            
            return {
                "markdown_path": md_path,
                "html_path": html_path,
                "extracted_text_path": extracted_path,
                "report_directory": report_dir
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنتاج التقرير: {e}")
            raise
    
    def _generate_markdown_report(self, data: ReportData, include_extracted_text: bool) -> str:
        """إنتاج تقرير Markdown"""
        
        new_questions = data.text_analysis.get("new_questions", [])
        new_explanations = data.text_analysis.get("new_explanations", [])
        has_significant_changes = data.text_analysis.get("has_significant_changes", False)
        
        md_content = f"""# تقرير مقارنة المناهج التعليمية

**معرف الجلسة:** {data.session_id}  
**تاريخ المعالجة:** {datetime.fromisoformat(data.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

---

## ملخص المقارنة

| العنصر | القيمة |
|---------|--------|
| الصورة القديمة | {data.old_image_name} |
| الصورة الجديدة | {data.new_image_name} |
| نسبة التشابه البصري | {data.visual_similarity:.1f}% |
| نسبة التشابه النصي | {data.text_analysis.get('similarity_percentage', 0):.1f}% |
| التغييرات الجوهرية | {"نعم" if has_significant_changes else "لا"} |

---
"""

        if new_questions:
            md_content += "\n## الأسئلة الجديدة 🆕\n\n"
            for i, question in enumerate(new_questions, 1):
                md_content += f"{i}. {question}\n"
            md_content += "\n---\n"

        if new_explanations:
            md_content += "\n## الشروحات الجديدة 📚\n\n"
            for i, explanation in enumerate(new_explanations, 1):
                md_content += f"{i}. {explanation}\n"
            md_content += "\n---\n"

        md_content += f"""
## تحليل المقارنة

### الملخص
{data.text_analysis.get('summary', 'لا يوجد ملخص متاح')}

### التوصيات
{data.text_analysis.get('recommendation', 'لا توجد توصيات متاحة')}
"""

        if data.text_analysis.get('major_differences'):
            md_content += "\n### الاختلافات الجوهرية\n"
            for diff in data.text_analysis['major_differences']:
                md_content += f"- {diff}\n"

        md_content += f"""
---

## إحصائيات المعالجة

| المرحلة | الوقت (ثانية) |
|----------|---------------|
| استخراج النص القديم | {data.processing_time.get('old_ocr', 0):.2f} |
| استخراج النص الجديد | {data.processing_time.get('new_ocr', 0):.2f} |
| تحليل المقارنة | {data.processing_time.get('comparison', 0):.2f} |
| **الإجمالي** | **{sum(data.processing_time.values()):.2f}** |

---
"""

        if include_extracted_text:
            md_content += f"""
## النصوص المستخرجة

### النص القديم
```
{data.old_extracted_text}
```

### النص الجديد
```
{data.new_extracted_text}
```
"""

        md_content += "\n---\n\n*تم إنتاج هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية*"
        
        return md_content
    
    def _generate_html_report(self, data: ReportData, include_visual_analysis: bool) -> str:
        """إنتاج تقرير HTML"""
        
        new_questions = data.text_analysis.get("new_questions", [])
        new_explanations = data.text_analysis.get("new_explanations", [])
        major_differences = data.text_analysis.get("major_differences", [])
        has_significant_changes = data.text_analysis.get("has_significant_changes", False)
        
        html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير مقارنة المناهج التعليمية</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007bff;
            margin: 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1.2em;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .new-content {{
            background-color: #e8f5e8;
            border-right: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .new-content h3 {{
            color: #28a745;
            margin-top: 0;
        }}
        .differences {{
            background-color: #fff3cd;
            border-right: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .differences h3 {{
            color: #856404;
            margin-top: 0;
        }}
        .list-item {{
            background-color: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-radius: 5px;
            border-right: 3px solid #007bff;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .stats-table th,
        .stats-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: center;
        }}
        .stats-table th {{
            background-color: #007bff;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 5px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 تقرير مقارنة المناهج التعليمية</h1>
            <p><strong>معرف الجلسة:</strong> {data.session_id}</p>
            <p><strong>تاريخ المعالجة:</strong> {datetime.fromisoformat(data.timestamp).strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>التشابه البصري</h3>
                <div class="value">{data.visual_similarity:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>التشابه النصي</h3>
                <div class="value">{data.text_analysis.get('similarity_percentage', 0):.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>التغييرات الجوهرية</h3>
                <div class="value">{"نعم" if has_significant_changes else "لا"}</div>
            </div>
        </div>
"""

        if new_questions:
            html_content += """
        <div class="new-content">
            <h3>🆕 الأسئلة الجديدة</h3>"""
            for i, question in enumerate(new_questions, 1):
                html_content += f"""
            <div class="list-item">
                <strong>{i}.</strong> {question}
            </div>"""
            html_content += """
        </div>"""

        if new_explanations:
            html_content += """
        <div class="new-content">
            <h3>📚 الشروحات الجديدة</h3>"""
            for i, explanation in enumerate(new_explanations, 1):
                html_content += f"""
            <div class="list-item">
                <strong>{i}.</strong> {explanation}
            </div>"""
            html_content += """
        </div>"""

        if major_differences:
            html_content += """
        <div class="differences">
            <h3>⚠️ الاختلافات الجوهرية</h3>"""
            for diff in major_differences:
                html_content += f"""
            <div class="list-item">
                • {diff}
            </div>"""
            html_content += """
        </div>"""

        html_content += f"""
        <h2>📊 تحليل المقارنة</h2>
        
        <h3>الملخص</h3>
        <p>{data.text_analysis.get('summary', 'لا يوجد ملخص متاح')}</p>
        
        <h3>التوصيات</h3>
        <p class="highlight">{data.text_analysis.get('recommendation', 'لا توجد توصيات متاحة')}</p>

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
                    <td>{data.processing_time.get('old_ocr', 0):.2f}</td>
                </tr>
                <tr>
                    <td>استخراج النص الجديد</td>
                    <td>{data.processing_time.get('new_ocr', 0):.2f}</td>
                </tr>
                <tr>
                    <td>تحليل المقارنة</td>
                    <td>{data.processing_time.get('comparison', 0):.2f}</td>
                </tr>
                <tr style="background-color: #e9ecef; font-weight: bold;">
                    <td>الإجمالي</td>
                    <td>{sum(data.processing_time.values()):.2f}</td>
                </tr>
            </tbody>
        </table>

        <div class="footer">
            <p><em>تم إنتاج هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية</em></p>
        </div>
    </div>
</body>
</html>"""
        
        return html_content
    
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

    async def health_check(self) -> Dict[str, Any]:
        """فحص صحة الخدمة"""
        return {
            "service": "EnhancedReportService",
            "status": "healthy",
            "output_directory": self.output_dir
        }
