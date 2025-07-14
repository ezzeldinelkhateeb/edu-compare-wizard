"""
خدمة إنتاج تقارير المقارنة الجماعية
Batch Comparison Report Generation Service
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
from jinja2 import Template
from loguru import logger

from app.core.config import get_settings

settings = get_settings()

class BatchReportService:
    """خدمة إنتاج تقارير المقارنة الجماعية"""
    
    def __init__(self):
        self.output_dir = os.path.join(settings.UPLOAD_DIR, "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("✅ تم تكوين خدمة تقارير المقارنة الجماعية")
    
    async def generate_batch_report(
        self,
        session_id: str,
        results: List[Dict[str, Any]],
        stats: Dict[str, Any],
        format_type: str = "both"  # "html", "md", or "both"
    ) -> Dict[str, str]:
        """إنتاج تقرير للمقارنة الجماعية"""
        logger.info(f"📋 إنشاء تقرير المقارنة الجماعية للجلسة: {session_id}")
        
        try:
            # إنشاء مجلد التقرير
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = os.path.join(self.output_dir, f"batch_report_{session_id}_{timestamp}")
            os.makedirs(report_dir, exist_ok=True)
            
            report_paths = {}
            
            # إنتاج تقرير Markdown إذا مطلوب
            if format_type in ["md", "both"]:
                md_content = self._generate_markdown_report(session_id, results, stats)
                md_path = os.path.join(report_dir, f"تقرير-شامل-session-{session_id}-{timestamp}.md")
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                report_paths["markdown_path"] = md_path
            
            # إنتاج تقرير HTML إذا مطلوب
            if format_type in ["html", "both"]:
                html_content = self._generate_html_report(session_id, results, stats)
                html_path = os.path.join(report_dir, f"تقرير-شامل-session-{session_id}-{timestamp}.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                report_paths["html_path"] = html_path
            
            report_paths["report_directory"] = report_dir
            
            logger.info(f"✅ تم إنتاج تقرير المقارنة الجماعية: {report_dir}")
            
            return report_paths
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنتاج تقرير المقارنة الجماعية: {e}")
            raise
    
    def _generate_markdown_report(self, session_id: str, results: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """إنتاج تقرير Markdown للمقارنة الجماعية"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # بداية التقرير
        md_content = f"""# تقرير مقارنة المناهج التعليمية الشامل

**معرف الجلسة:** {session_id}  
**تاريخ التقرير:** {timestamp}

---

## ملخص المقارنة الجماعية

| العنصر | القيمة |
|---------|--------|
| إجمالي الأزواج | {stats.get('total_pairs', 0)} |
| تطابق بصري عالي | {stats.get('visually_identical', 0)} ({stats.get('visually_identical', 0)/stats.get('total_pairs', 1)*100:.1f}%) |
| تحليل كامل | {stats.get('fully_analyzed', 0)} ({stats.get('fully_analyzed', 0)/stats.get('total_pairs', 1)*100:.1f}%) |
| فشل في المعالجة | {stats.get('failed', 0)} ({stats.get('failed', 0)/stats.get('total_pairs', 1)*100:.1f}%) |
| المدة الإجمالية | {stats.get('total_duration', 0):.2f} ثانية |
| متوسط الوقت لكل زوج | {stats.get('total_duration', 0)/stats.get('total_pairs', 1):.2f} ثانية |

---

## تفاصيل المقارنات

"""
        
        # إضافة تفاصيل كل مقارنة
        for result in results:
            md_content += f"""### {result.get('filename', 'غير معروف')}

**الصورة القديمة:** {result.get('old_filename', 'غير معروف')}  
**الصورة الجديدة:** {result.get('new_filename', 'غير معروف')}  
**نسبة التشابه البصري:** {result.get('visual_score', 0)*100:.1f}%  
"""
            
            # إضافة تفاصيل إضافية حسب حالة المعالجة
            if result.get('status') == 'تطابق بصري عالي':
                md_content += "**النتيجة:** تطابق بصري عالي - توقف المعالجة\n\n"
            elif result.get('status') in ['تم التحليل الكامل', 'تم التحليل الكامل (Gemini Vision)']:
                md_content += f"""**نسبة التشابه النهائية:** {result.get('final_score', 0):.1f}%  
**ملخص التغييرات:** {result.get('summary', 'لا يوجد ملخص')}

"""
                
                # إضافة تفاصيل التحليل إذا كانت متوفرة
                ai_analysis = result.get('ai_analysis', {})
                if ai_analysis:
                    content_changes = ai_analysis.get('content_changes', [])
                    if content_changes:
                        md_content += "#### التغييرات في المحتوى\n\n"
                        for change in content_changes:
                            md_content += f"- {change}\n"
                        md_content += "\n"
            
            elif result.get('status') == 'فشل':
                md_content += f"**خطأ:** {result.get('error', 'خطأ غير محدد')}\n\n"
            
            md_content += "---\n\n"
        
        # إضافة تذييل التقرير
        md_content += """## ملاحظات

- التشابه البصري يعتمد على مقارنة الصور باستخدام خوارزميات متقدمة
- التحليل النصي يستخدم تقنيات معالجة اللغة الطبيعية لاستخراج وتحليل المحتوى

---

*تم إنتاج هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية*
"""
        
        return md_content
    
    def _generate_html_report(self, session_id: str, results: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """إنتاج تقرير HTML للمقارنة الجماعية"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # بداية التقرير
        html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير مقارنة المناهج التعليمية الشامل</title>
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
        .comparison-card {{
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            padding: 20px;
            border-right: 4px solid #007bff;
        }}
        .comparison-card h3 {{
            margin-top: 0;
            color: #007bff;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        .comparison-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 15px;
        }}
        .image-info {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }}
        .similarity-bar {{
            height: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .similarity-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #17a2b8);
        }}
        .changes-list {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }}
        .changes-list h4 {{
            margin-top: 0;
            color: #6c757d;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
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
        .error-message {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }}
        
        /* تنسيقات جديدة للتغييرات */
        .changes-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .changes-box {{
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .changes-box h4 {{
            margin-top: 0;
            display: flex;
            align-items: center;
            font-size: 16px;
        }}
        .changes-box h4 i {{
            margin-left: 8px;
            font-size: 18px;
        }}
        .changes-box ul {{
            margin: 0;
            padding-right: 20px;
        }}
        .changes-box li {{
            margin-bottom: 8px;
        }}
        
        /* ألوان مختلفة للتغييرات */
        .new-questions {{
            background-color: #d4edda;
            border-right: 4px solid #28a745;
        }}
        .new-questions h4 {{
            color: #155724;
        }}
        .deleted-questions {{
            background-color: #f8d7da;
            border-right: 4px solid #dc3545;
        }}
        .deleted-questions h4 {{
            color: #721c24;
        }}
        .new-explanations {{
            background-color: #cce5ff;
            border-right: 4px solid #007bff;
        }}
        .new-explanations h4 {{
            color: #004085;
        }}
        .deleted-explanations {{
            background-color: #fff3cd;
            border-right: 4px solid #ffc107;
        }}
        .deleted-explanations h4 {{
            color: #856404;
        }}
        .new-examples {{
            background-color: #d1ecf1;
            border-right: 4px solid #17a2b8;
        }}
        .new-examples h4 {{
            color: #0c5460;
        }}
        .deleted-examples {{
            background-color: #e2e3e5;
            border-right: 4px solid #6c757d;
        }}
        .deleted-examples h4 {{
            color: #383d41;
        }}
        .numerical-changes {{
            background-color: #f5f0ff;
            border-right: 4px solid #6f42c1;
        }}
        .numerical-changes h4 {{
            color: #6f42c1;
        }}
        
        /* أيقونات للتغييرات */
        @font-face {{
            font-family: 'Material Icons';
            font-style: normal;
            font-weight: 400;
            src: url(https://fonts.gstatic.com/s/materialicons/v139/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2) format('woff2');
        }}
        .material-icons {{
            font-family: 'Material Icons';
            font-weight: normal;
            font-style: normal;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 تقرير مقارنة المناهج التعليمية الشامل</h1>
            <p><strong>معرف الجلسة:</strong> {session_id}</p>
            <p><strong>تاريخ التقرير:</strong> {timestamp}</p>
        </div>

        <h2>ملخص المقارنة الجماعية</h2>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>إجمالي الأزواج</h3>
                <div class="value">{stats.get('total_pairs', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>تطابق بصري عالي</h3>
                <div class="value">{stats.get('visually_identical', 0)}</div>
                <div>({stats.get('visually_identical', 0)/stats.get('total_pairs', 1)*100:.1f}%)</div>
            </div>
            <div class="summary-card">
                <h3>تحليل كامل</h3>
                <div class="value">{stats.get('fully_analyzed', 0)}</div>
                <div>({stats.get('fully_analyzed', 0)/stats.get('total_pairs', 1)*100:.1f}%)</div>
            </div>
            <div class="summary-card">
                <h3>فشل في المعالجة</h3>
                <div class="value">{stats.get('failed', 0)}</div>
                <div>({stats.get('failed', 0)/stats.get('total_pairs', 1)*100:.1f}%)</div>
            </div>
        </div>

        <h2>إحصائيات الأداء</h2>
        <table class="stats-table">
            <tr>
                <th>المدة الإجمالية</th>
                <th>متوسط الوقت لكل زوج</th>
                <th>متوسط التوفير في التكلفة</th>
            </tr>
            <tr>
                <td>{stats.get('total_duration', 0):.2f} ثانية</td>
                <td>{stats.get('total_duration', 0)/stats.get('total_pairs', 1):.2f} ثانية</td>
                <td>
                    {(stats.get('visually_identical', 0)/stats.get('total_pairs', 1)*100) + (stats.get('fully_analyzed', 0)/stats.get('total_pairs', 1)*33.3):.1f}%
                </td>
            </tr>
        </table>

        <h2>تفاصيل المقارنات</h2>
"""
        
        # إضافة تفاصيل كل مقارنة
        for result in results:
            visual_score = result.get('visual_score', 0) * 100
            final_score = result.get('final_score', visual_score)
            
            html_content += f"""
        <div class="comparison-card">
            <h3>{result.get('filename', 'غير معروف')}</h3>
            
            <div class="comparison-details">
                <div class="image-info">
                    <strong>الصورة القديمة:</strong> {result.get('old_filename', 'غير معروف')}<br>
                    <strong>الصورة الجديدة:</strong> {result.get('new_filename', 'غير معروف')}
                </div>
                
                <div class="similarity-info">
                    <strong>نسبة التشابه البصري:</strong> {visual_score:.1f}%
                    <div class="similarity-bar">
                        <div class="similarity-fill" style="width: {visual_score}%"></div>
                    </div>
"""
            
            # إضافة تفاصيل إضافية حسب حالة المعالجة
            if result.get('status') == 'تطابق بصري عالي':
                html_content += f"""
                    <strong>النتيجة:</strong> تطابق بصري عالي - توقف المعالجة
                </div>
            </div>
"""
            elif result.get('status') in ['تم التحليل الكامل', 'تم التحليل الكامل (Gemini Vision)']:
                html_content += f"""
                    <strong>نسبة التشابه النهائية:</strong> {final_score:.1f}%
                    <div class="similarity-bar">
                        <div class="similarity-fill" style="width: {final_score}%"></div>
                    </div>
                </div>
            </div>
            
            <strong>ملخص التغييرات:</strong> {result.get('summary', 'لا يوجد ملخص')}
"""
                
                # إضافة تفاصيل التحليل إذا كانت متوفرة
                ai_analysis = result.get('ai_analysis', {})
                if ai_analysis:
                    # التحقق من وجود أي تغييرات
                    has_changes = False
                    for key in ['new_questions', 'deleted_questions', 'new_explanations', 'deleted_explanations', 
                               'new_examples', 'deleted_examples', 'numerical_changes']:
                        if ai_analysis.get(key, []):
                            has_changes = True
                            break
                    
                    if has_changes:
                        html_content += """
            <div class="changes-container">
"""
                        
                        # إضافة الأسئلة الجديدة
                        new_questions = ai_analysis.get('new_questions', [])
                        if new_questions:
                            html_content += """
                <div class="changes-box new-questions">
                    <h4><i class="material-icons">add_circle</i> الأسئلة الجديدة</h4>
                    <ul>
"""
                            for question in new_questions:
                                html_content += f"                        <li>{question}</li>\n"
                            html_content += "                    </ul>\n                </div>\n"
                        
                        # إضافة الأسئلة المحذوفة
                        deleted_questions = ai_analysis.get('deleted_questions', [])
                        if deleted_questions:
                            html_content += """
                <div class="changes-box deleted-questions">
                    <h4><i class="material-icons">remove_circle</i> الأسئلة المحذوفة</h4>
                    <ul>
"""
                            for question in deleted_questions:
                                html_content += f"                        <li>{question}</li>\n"
                            html_content += "                    </ul>\n                </div>\n"
                        
                        # إضافة الشروحات الجديدة
                        new_explanations = ai_analysis.get('new_explanations', [])
                        if new_explanations:
                            html_content += """
                <div class="changes-box new-explanations">
                    <h4><i class="material-icons">school</i> الشروحات الجديدة</h4>
                    <ul>
"""
                            for explanation in new_explanations:
                                html_content += f"                        <li>{explanation}</li>\n"
                            html_content += "                    </ul>\n                </div>\n"
                        
                        # إضافة الشروحات المحذوفة
                        deleted_explanations = ai_analysis.get('deleted_explanations', [])
                        if deleted_explanations:
                            html_content += """
                <div class="changes-box deleted-explanations">
                    <h4><i class="material-icons">school</i> الشروحات المحذوفة</h4>
                    <ul>
"""
                            for explanation in deleted_explanations:
                                html_content += f"                        <li>{explanation}</li>\n"
                            html_content += "                    </ul>\n                </div>\n"
                        
                        # إضافة الأمثلة الجديدة
                        new_examples = ai_analysis.get('new_examples', [])
                        if new_examples:
                            html_content += """
                <div class="changes-box new-examples">
                    <h4><i class="material-icons">lightbulb</i> الأمثلة الجديدة</h4>
                    <ul>
"""
                            for example in new_examples:
                                html_content += f"                        <li>{example}</li>\n"
                            html_content += "                    </ul>\n                </div>\n"
                        
                        # إضافة الأمثلة المحذوفة
                        deleted_examples = ai_analysis.get('deleted_examples', [])
                        if deleted_examples:
                            html_content += """
                <div class="changes-box deleted-examples">
                    <h4><i class="material-icons">lightbulb_outline</i> الأمثلة المحذوفة</h4>
                    <ul>
"""
                            for example in deleted_examples:
                                html_content += f"                        <li>{example}</li>\n"
                            html_content += "                    </ul>\n                </div>\n"
                        
                        # إضافة التغييرات في الأرقام
                        numerical_changes = ai_analysis.get('numerical_changes', [])
                        if numerical_changes:
                            html_content += """
                <div class="changes-box numerical-changes">
                    <h4><i class="material-icons">functions</i> التغييرات في الأرقام</h4>
                    <ul>
"""
                            for change in numerical_changes:
                                html_content += f"                        <li>{change}</li>\n"
                            html_content += "                    </ul>\n                </div>\n"
                        
                        html_content += "            </div>\n"
                    
                    # إضافة التغييرات العامة في المحتوى
                    content_changes = ai_analysis.get('content_changes', [])
                    if content_changes:
                        html_content += """
            <div class="changes-list">
                <h4>التغييرات في المحتوى</h4>
                <ul>
"""
                        for change in content_changes:
                            html_content += f"                    <li>{change}</li>\n"
                        html_content += "                </ul>\n            </div>\n"
            
            elif result.get('status') == 'فشل':
                html_content += f"""
                </div>
            </div>
            <div class="error-message">
                <strong>خطأ:</strong> {result.get('error', 'خطأ غير محدد')}
            </div>
"""
            
            html_content += "        </div>\n"
        
        # إضافة تذييل التقرير
        html_content += """
        <div class="footer">
            <p><em>تم إنتاج هذا التقرير تلقائياً بواسطة نظام مقارن المناهج التعليمية</em></p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content 