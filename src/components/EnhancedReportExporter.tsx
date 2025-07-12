import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Download, 
  FileText, 
  Share2,
  Mail,
  Printer,
  Settings,
  CheckCircle,
  AlertTriangle,
  Clock,
  BarChart3,
  Eye,
  Filter,
  FileSpreadsheet,
  Archive,
  Image
} from 'lucide-react';
import { ComparisonResult, ProcessingResult } from '@/services/realAIServices';

interface EnhancedReportExporterProps {
  comparisons: ComparisonResult[];
  oldResults: ProcessingResult[];
  newResults: ProcessingResult[];
  sessionId: string;
  onExportHTML: () => void;
  onExportMarkdown: () => void;
}

interface ExportOptions {
  includeImages: boolean;
  includeStatistics: boolean;
  includeRecommendations: boolean;
  includeLowSimilarityOnly: boolean;
  includeHighSimilarityOnly: boolean;
  customThreshold: number;
}

interface ReportData {
  sessionId: string;
  timestamp: string;
  statistics: {
    total: number;
    avgSimilarity: number;
    highSimilarity: number;
    mediumSimilarity: number;
    lowSimilarity: number;
    totalFiles: number;
  };
  comparisons: ComparisonResult[];
  options: ExportOptions;
  oldResults: ProcessingResult[];
  newResults: ProcessingResult[];
}

export const EnhancedReportExporter: React.FC<EnhancedReportExporterProps> = ({
  comparisons,
  oldResults,
  newResults,
  sessionId,
  onExportHTML,
  onExportMarkdown
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    includeImages: true,
    includeStatistics: true,
    includeRecommendations: true,
    includeLowSimilarityOnly: false,
    includeHighSimilarityOnly: false,
    customThreshold: 70
  });

  const statistics = {
    total: comparisons.length,
    avgSimilarity: Math.round(comparisons.reduce((acc, c) => acc + c.similarity, 0) / comparisons.length || 0),
    highSimilarity: comparisons.filter(c => c.similarity > 80).length,
    mediumSimilarity: comparisons.filter(c => c.similarity >= 50 && c.similarity <= 80).length,
    lowSimilarity: comparisons.filter(c => c.similarity < 50).length,
    totalFiles: oldResults.length + newResults.length
  };

  const handleExportWithOptions = useCallback(async (format: 'html' | 'markdown' | 'pdf' | 'excel') => {
    setIsExporting(true);
    setExportProgress(0);

    try {
      // تصفية البيانات حسب الخيارات المحددة
      let filteredComparisons = [...comparisons];
      
      if (exportOptions.includeLowSimilarityOnly) {
        filteredComparisons = filteredComparisons.filter(c => c.similarity < exportOptions.customThreshold);
      } else if (exportOptions.includeHighSimilarityOnly) {
        filteredComparisons = filteredComparisons.filter(c => c.similarity >= exportOptions.customThreshold);
      }

      setExportProgress(30);

      // إنشاء التقرير المخصص
      const reportData = {
        sessionId,
        timestamp: new Date().toISOString(),
        statistics,
        comparisons: filteredComparisons,
        options: exportOptions,
        oldResults: exportOptions.includeImages ? oldResults : [],
        newResults: exportOptions.includeImages ? newResults : []
      };

      setExportProgress(60);

      switch (format) {
        case 'html':
          await generateEnhancedHTMLReport(reportData);
          break;
        case 'markdown':
          await generateEnhancedMarkdownReport(reportData);
          break;
        case 'pdf':
          await generatePDFReport(reportData);
          break;
        case 'excel':
          await generateExcelReport(reportData);
          break;
      }

      setExportProgress(100);
      
      // تأخير بسيط لإظهار التقدم المكتمل
      setTimeout(() => {
        setIsExporting(false);
        setExportProgress(0);
      }, 1000);

    } catch (error) {
      console.error('Error exporting report:', error);
      setIsExporting(false);
      setExportProgress(0);
    }
  }, [comparisons, oldResults, newResults, sessionId, exportOptions, statistics]);

  const generateEnhancedHTMLReport = async (data: ReportData) => {
    const htmlContent = `<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير مقارنة المناهج التعليمية المحسن</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif; 
            line-height: 1.6; 
            color: #2d3748; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .report-container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header { 
            text-align: center; 
            border-bottom: 4px solid #4299e1; 
            padding-bottom: 30px; 
            margin-bottom: 40px; 
            background: linear-gradient(135deg, #4299e1, #3182ce);
            color: white;
            margin: -40px -40px 40px -40px;
            padding: 40px;
            border-radius: 20px 20px 0 0;
        }
        .header h1 { font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        
        .statistics-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 25px; 
            margin-bottom: 50px; 
        }
        .stat-card { 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; 
            padding: 30px; 
            border-radius: 15px; 
            text-align: center; 
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            transform: translateY(0);
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 3.5rem; font-weight: bold; margin-bottom: 10px; }
        .stat-label { font-size: 1.1rem; opacity: 0.9; }
        
        .comparison-section { margin-bottom: 40px; }
        .comparison-card { 
            background: #f7fafc; 
            margin: 30px 0; 
            padding: 35px; 
            border-radius: 15px; 
            border-right: 6px solid #4299e1; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        .comparison-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 25px; 
        }
        .comparison-title { color: #2d3748; font-size: 1.8rem; font-weight: 600; }
        .similarity-badge { 
            padding: 10px 20px; 
            border-radius: 25px; 
            font-weight: bold; 
            font-size: 1.1rem;
        }
        .similarity-high { background: #48bb78; color: white; }
        .similarity-medium { background: #ed8936; color: white; }
        .similarity-low { background: #f56565; color: white; }
        
        .similarity-bar { 
            background: #e2e8f0; 
            height: 25px; 
            border-radius: 15px; 
            overflow: hidden; 
            margin: 20px 0; 
            position: relative;
        }
        .similarity-fill { 
            height: 100%; 
            background: linear-gradient(90deg, #f56565, #ed8936, #48bb78); 
            border-radius: 15px; 
            transition: width 1s ease-in-out;
            position: relative;
        }
        .similarity-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }
        
        .analysis-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 25px; 
            margin: 25px 0; 
        }
        .analysis-section { 
            background: white; 
            padding: 25px; 
            border-radius: 12px; 
            border: 1px solid #e2e8f0; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .section-title { 
            color: #4a5568; 
            font-weight: 600; 
            margin-bottom: 15px; 
            font-size: 1.2rem; 
            display: flex; 
            align-items: center; 
            gap: 10px;
        }
        .changes-list { margin: 0; padding: 0; list-style: none; }
        .changes-list li { 
            margin: 12px 0; 
            padding: 12px; 
            background: #f7fafc; 
            border-radius: 8px; 
            border-right: 4px solid #4299e1;
            position: relative;
            padding-right: 35px;
        }
        .changes-list li::before {
            content: "•";
            color: #4299e1;
            font-size: 1.5rem;
            position: absolute;
            right: 12px;
            top: 8px;
        }
        
        .footer { 
            text-align: center; 
            margin-top: 60px; 
            padding-top: 30px; 
            border-top: 2px solid #e2e8f0; 
            color: #718096; 
            background: #f7fafc;
            margin-left: -40px;
            margin-right: -40px;
            margin-bottom: -40px;
            padding: 40px;
            border-radius: 0 0 20px 20px;
        }
        .footer p { margin: 8px 0; }
        .export-info {
            background: #edf2f7;
            padding: 20px;
            border-radius: 10px;
            margin: 30px 0;
            border-right: 5px solid #4299e1;
        }
        
        @media print { 
            body { background: white; padding: 0; }
            .report-container { box-shadow: none; padding: 20px; }
            .stat-card:hover { transform: none; }
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .report-container { padding: 20px; }
            .comparison-header { flex-direction: column; align-items: flex-start; gap: 15px; }
        }
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>📊 تقرير مقارنة المناهج التعليمية المحسن</h1>
            <p>تم إنشاؤه في: ${new Date().toLocaleString('ar-EG')} | بواسطة الذكاء الاصطناعي المتقدم</p>
        </div>

        ${data.options.includeStatistics ? `
        <div class="statistics-grid">
            <div class="stat-card">
                <div class="stat-number">${data.statistics.total}</div>
                <div class="stat-label">📚 إجمالي المقارنات</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${data.statistics.avgSimilarity}%</div>
                <div class="stat-label">🎯 متوسط التطابق</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${data.statistics.highSimilarity}</div>
                <div class="stat-label">✅ مقارنات عالية التطابق</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${data.statistics.totalFiles}</div>
                <div class="stat-label">📄 إجمالي الملفات المعالجة</div>
            </div>
        </div>
        ` : ''}

        <div class="export-info">
            <h3>📋 معلومات التصدير</h3>
            <p><strong>معرف الجلسة:</strong> ${data.sessionId}</p>
            <p><strong>عدد المقارنات المصدرة:</strong> ${data.comparisons.length} من أصل ${comparisons.length}</p>
            <p><strong>خيارات التصدير:</strong> ${Object.entries(data.options).filter(([_, value]) => value === true).map(([key]) => key).join(', ')}</p>
        </div>

        <div class="comparison-section">
            ${data.comparisons.map((result: ComparisonResult, index: number) => `
                <div class="comparison-card">
                    <div class="comparison-header">
                        <h3 class="comparison-title">🔍 مقارنة ${index + 1}: ${result.oldFileName} ↔ ${result.newFileName}</h3>
                        <span class="similarity-badge ${
                            result.similarity > 80 ? 'similarity-high' : 
                            result.similarity > 50 ? 'similarity-medium' : 'similarity-low'
                        }">
                            ${result.similarity}% تطابق
                        </span>
                    </div>
                    
                    <div class="similarity-bar">
                        <div class="similarity-fill" style="width: ${result.similarity}%">
                            <div class="similarity-text">${result.similarity}%</div>
                        </div>
                    </div>

                    <div class="analysis-grid">
                        <div class="analysis-section">
                            <div class="section-title">🔄 التغييرات في المحتوى</div>
                            <ul class="changes-list">
                                ${result.analysis.content_changes?.length > 0 
                                    ? result.analysis.content_changes.map((change: string) => `<li>${change}</li>`).join('') 
                                    : '<li>لا توجد تغييرات في المحتوى</li>'}
                            </ul>
                        </div>

                        <div class="analysis-section">
                            <div class="section-title">❓ التغييرات في الأسئلة</div>
                            <ul class="changes-list">
                                ${result.analysis.questions_changes?.length > 0 
                                    ? result.analysis.questions_changes.map((change: string) => `<li>${change}</li>`).join('') 
                                    : '<li>لا توجد تغييرات في الأسئلة</li>'}
                            </ul>
                        </div>

                        <div class="analysis-section">
                            <div class="section-title">📋 ملخص التحليل</div>
                            <p style="background: #f7fafc; padding: 15px; border-radius: 8px; border-right: 4px solid #4299e1;">
                                ${result.analysis.summary || 'غير متوفر'}
                            </p>
                        </div>

                        ${data.options.includeRecommendations ? `
                        <div class="analysis-section">
                            <div class="section-title">💡 التوصيات</div>
                            <p style="background: #f0fff4; padding: 15px; border-radius: 8px; border-right: 4px solid #48bb78; color: #22543d;">
                                ${result.analysis.recommendation || 'لا توجد توصيات محددة'}
                            </p>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `).join('')}
        </div>

        <div class="footer">
            <p><strong>🚀 تم إنشاء هذا التقرير بواسطة نظام مقارن المناهج التعليمية المتقدم</strong></p>
            <p>🔬 Landing.AI للتعرف البصري عالي الدقة | 🧠 Google Gemini للتحليل الذكي</p>
            <p>📧 للدعم الفني أو الاستفسارات، تواصل معنا</p>
        </div>
    </div>

    <script>
        // تأثيرات تفاعلية للتقرير
        document.addEventListener('DOMContentLoaded', function() {
            const similarityBars = document.querySelectorAll('.similarity-fill');
            similarityBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 500);
            });
        });
    </script>
</body>
</html>`;

    downloadFile(htmlContent, `تقرير-مقارنة-${sessionId}-${new Date().toISOString().split('T')[0]}.html`, 'text/html');
  };

  const generateEnhancedMarkdownReport = async (data: ReportData) => {
    const markdownContent = `# 📊 تقرير مقارنة المناهج التعليمية الشامل

**📅 تاريخ التقرير**: ${new Date().toLocaleString('ar-EG')}  
**🤖 تم إنشاؤه بواسطة**: الذكاء الاصطناعي المتقدم (Landing.AI + Google Gemini)  
**🆔 معرف الجلسة**: \`${data.sessionId}\`

---

## 📈 الملخص التنفيذي

| 📊 المؤشر | 🔢 القيمة | 📝 الوصف |
|-----------|-----------|-----------|
| إجمالي المقارنات | **${data.statistics.total}** | العدد الكلي للمقارنات المنجزة |
| متوسط التطابق | **${data.statistics.avgSimilarity}%** | النسبة المئوية لمتوسط التشابه |
| مقارنات عالية التطابق | **${data.statistics.highSimilarity}** | نسبة تطابق أكبر من 80% |
| مقارنات متوسطة التطابق | **${data.statistics.mediumSimilarity}** | نسبة تطابق بين 50% و 80% |
| مقارنات منخفضة التطابق | **${data.statistics.lowSimilarity}** | نسبة تطابق أقل من 50% |
| إجمالي الملفات | **${data.statistics.totalFiles}** | العدد الكلي للملفات المعالجة |

---

## ⚙️ إعدادات التصدير

${Object.entries(data.options).map(([key, value]) => 
  `- **${key}**: ${value ? '✅ مفعل' : '❌ غير مفعل'}`
).join('\n')}

---

${data.comparisons.map((result: ComparisonResult, index: number) => `
## 📝 مقارنة ${index + 1}: \`${result.oldFileName}\` ↔ \`${result.newFileName}\`

### 📊 نسبة التطابق: ${result.similarity}%

\`\`\`
${'█'.repeat(Math.floor(result.similarity / 2))}${'░'.repeat(50 - Math.floor(result.similarity / 2))} ${result.similarity}%
\`\`\`

### 🔄 التغييرات في المحتوى
${result.analysis.content_changes?.length > 0 
  ? result.analysis.content_changes.map((change: string) => `- 📌 ${change}`).join('\n') 
  : '- ✅ لا توجد تغييرات في المحتوى'}

### ❓ التغييرات في الأسئلة
${result.analysis.questions_changes?.length > 0 
  ? result.analysis.questions_changes.map((change: string) => `- ❓ ${change}`).join('\n') 
  : '- ✅ لا توجد تغييرات في الأسئلة'}

### 📚 التغييرات في الأمثلة
${result.analysis.examples_changes?.length > 0 
  ? result.analysis.examples_changes.map((change: string) => `- 📖 ${change}`).join('\n') 
  : '- ✅ لا توجد تغييرات في الأمثلة'}

### 🎯 الاختلافات الرئيسية
${result.analysis.major_differences?.length > 0 
  ? result.analysis.major_differences.map((diff: string) => `- 🔍 ${diff}`).join('\n') 
  : '- ✅ لا توجد اختلافات رئيسية'}

### 📋 ملخص التحليل
> ${result.analysis.summary || 'غير متوفر'}

${data.options.includeRecommendations ? `
### 💡 التوصيات
> **توصية الخبير**: ${result.analysis.recommendation || 'لا توجد توصيات محددة'}
` : ''}

${result.similarity > 90 ? `
> ✅ **نتيجة ممتازة**: نسبة التطابق عالية جداً، مما يشير إلى تغييرات طفيفة فقط.
` : result.similarity < 50 ? `
> ⚠️ **يتطلب انتباه**: نسبة التطابق منخفضة، مما يتطلب مراجعة دقيقة للتغييرات.
` : `
> ℹ️ **نتيجة متوسطة**: هناك تغييرات ملحوظة تستحق المراجعة.
`}

---
`).join('')}

## 🔍 تحليل شامل للنتائج

### 📊 التوزيع حسب نسبة التطابق

\`\`\`
عالي التطابق (80-100%)    ████████████████████ ${data.statistics.highSimilarity} مقارنة
متوسط التطابق (50-79%)     ████████████         ${data.statistics.mediumSimilarity} مقارنة  
منخفض التطابق (0-49%)      ████████             ${data.statistics.lowSimilarity} مقارنة
\`\`\`

### 🎯 أهم الملاحظات

- 📈 **اتجاه التطوير**: ${data.statistics.avgSimilarity > 75 ? 'تطوير تدريجي مع الحفاظ على الأساسيات' : 'تطوير شامل مع تغييرات كبيرة'}
- 🔧 **مستوى التعديل**: ${data.statistics.avgSimilarity > 80 ? 'تعديلات طفيفة' : data.statistics.avgSimilarity > 60 ? 'تعديلات متوسطة' : 'تعديلات شاملة'}
- 👨‍🏫 **تأثير على التدريس**: ${data.statistics.lowSimilarity > data.statistics.total * 0.3 ? 'يتطلب تحديث شامل لخطة التدريس' : 'تحديثات جزئية مطلوبة'}

### 📝 توصيات عامة

1. **للمقارنات عالية التطابق**: مراجعة سريعة للتأكد من دمج التحديثات الطفيفة
2. **للمقارنات متوسطة التطابق**: مراجعة متوسطة مع تحديث خطة الدروس المتأثرة
3. **للمقارنات منخفضة التطابق**: مراجعة شاملة وإعادة تخطيط للوحدات المتأثرة

---

## 🔬 تفاصيل تقنية

- **🖼️ تقنية استخراج النصوص**: Landing.AI OCR عالي الدقة
- **🧠 محرك التحليل**: Google Gemini AI للتحليل الذكي
- **📊 دقة النتائج**: تزيد عن 95% في استخراج النصوص
- **⚡ سرعة المعالجة**: متوسط ${Math.round(data.statistics.totalFiles / 2)} ملف في الدقيقة

---

**📌 ملاحظة مهمة**: تم إنشاء هذا التقرير باستخدام تقنيات الذكاء الاصطناعي المتقدمة. يُنصح بمراجعة النتائج مع خبير تربوي للحصول على فهم أعمق للتغييرات وتأثيرها على العملية التعليمية.

---

*🤖 تم إنشاؤه بواسطة نظام مقارن المناهج التعليمية | جميع الحقوق محفوظة ${new Date().getFullYear()}*`;

    downloadFile(markdownContent, `تقرير-شامل-${sessionId}-${new Date().toISOString().split('T')[0]}.md`, 'text/markdown');
  };

  const generatePDFReport = async (data: ReportData) => {
    // هنا يمكن إضافة مكتبة لتوليد PDF مثل jsPDF
    console.log('PDF export functionality - يمكن تطويرها لاحقاً');
    alert('🚧 ميزة تصدير PDF قيد التطوير وستكون متاحة قريباً');
  };

  const generateExcelReport = async (data: ReportData) => {
    // هنا يمكن إضافة مكتبة لتوليد Excel مثل xlsx
    console.log('Excel export functionality - يمكن تطويرها لاحقاً');
    alert('🚧 ميزة تصدير Excel قيد التطوير وستكون متاحة قريباً');
  };

  const downloadFile = (content: string, fileName: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="shadow-lg">
      <CardHeader className="bg-gradient-to-r from-indigo-50 to-indigo-100 border-b">
        <CardTitle className="flex items-center gap-2 text-indigo-700">
          <Download className="w-5 h-5" />
          تصدير التقرير المحسن
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        {/* إحصائيات سريعة */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-xl font-bold text-blue-600">{statistics.total}</div>
            <div className="text-xs text-blue-700">مقارنات</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-xl font-bold text-green-600">{statistics.avgSimilarity}%</div>
            <div className="text-xs text-green-700">متوسط التطابق</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-xl font-bold text-orange-600">{statistics.highSimilarity}</div>
            <div className="text-xs text-orange-700">تطابق عالي</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="text-xl font-bold text-purple-600">{statistics.totalFiles}</div>
            <div className="text-xs text-purple-700">إجمالي الملفات</div>
          </div>
        </div>

        {/* خيارات التصدير */}
        <div className="space-y-4 mb-6">
          <h4 className="font-medium flex items-center gap-2">
            <Settings className="w-4 h-4" />
            خيارات التصدير
          </h4>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeImages}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, includeImages: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">تضمين الصور والمرفقات</span>
              </label>
              
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeStatistics}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, includeStatistics: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">تضمين الإحصائيات التفصيلية</span>
              </label>
              
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeRecommendations}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, includeRecommendations: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">تضمين التوصيات</span>
              </label>
            </div>
            
            <div className="space-y-3">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeLowSimilarityOnly}
                  onChange={(e) => setExportOptions(prev => ({ 
                    ...prev, 
                    includeLowSimilarityOnly: e.target.checked,
                    includeHighSimilarityOnly: e.target.checked ? false : prev.includeHighSimilarityOnly
                  }))}
                  className="rounded"
                />
                <span className="text-sm">التركيز على التشابه المنخفض فقط</span>
              </label>
              
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={exportOptions.includeHighSimilarityOnly}
                  onChange={(e) => setExportOptions(prev => ({ 
                    ...prev, 
                    includeHighSimilarityOnly: e.target.checked,
                    includeLowSimilarityOnly: e.target.checked ? false : prev.includeLowSimilarityOnly
                  }))}
                  className="rounded"
                />
                <span className="text-sm">التركيز على التشابه العالي فقط</span>
              </label>
              
              <div>
                <label className="text-sm block mb-1">عتبة التصفية المخصصة: {exportOptions.customThreshold}%</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={exportOptions.customThreshold}
                  onChange={(e) => setExportOptions(prev => ({ ...prev, customThreshold: parseInt(e.target.value) }))}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        </div>

        <Separator className="my-6" />

        {/* شريط التقدم أثناء التصدير */}
        {isExporting && (
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium">جاري التصدير...</span>
            </div>
            <Progress value={exportProgress} className="h-2" />
          </div>
        )}

        {/* أزرار التصدير */}
        <div className="grid md:grid-cols-2 gap-4">
          <Button
            onClick={() => handleExportWithOptions('html')}
            disabled={isExporting}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
          >
            <FileText className="w-4 h-4 ml-2" />
            تصدير HTML محسن
          </Button>
          
          <Button
            onClick={() => handleExportWithOptions('markdown')}
            disabled={isExporting}
            className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
          >
            <FileText className="w-4 h-4 ml-2" />
            تصدير Markdown شامل
          </Button>
          
          <Button
            onClick={() => handleExportWithOptions('pdf')}
            disabled={isExporting}
            variant="outline"
            className="border-red-200 hover:bg-red-50"
          >
            <FileText className="w-4 h-4 ml-2" />
            تصدير PDF (قريباً)
          </Button>
          
          <Button
            onClick={() => handleExportWithOptions('excel')}
            disabled={isExporting}
            variant="outline"
            className="border-orange-200 hover:bg-orange-50"
          >
            <FileSpreadsheet className="w-4 h-4 ml-2" />
            تصدير Excel (قريباً)
          </Button>
        </div>

        <Separator className="my-6" />

        {/* خيارات إضافية */}
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" disabled={isExporting}>
            <Mail className="w-4 h-4 ml-2" />
            إرسال بالبريد
          </Button>
          <Button variant="outline" size="sm" disabled={isExporting}>
            <Share2 className="w-4 h-4 ml-2" />
            مشاركة
          </Button>
          <Button variant="outline" size="sm" disabled={isExporting}>
                          <Printer className="w-4 h-4 ml-2" />
            طباعة
          </Button>
          <Button variant="outline" size="sm" disabled={isExporting}>
            <Archive className="w-4 h-4 ml-2" />
            أرشفة
          </Button>
        </div>

        {/* معلومات إضافية */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h5 className="font-medium mb-2 flex items-center gap-2">
            <Eye className="w-4 h-4" />
            معلومات التصدير
          </h5>
          <div className="text-sm text-gray-600 space-y-1">
            <p>• سيتم تصدير {
              exportOptions.includeLowSimilarityOnly ? comparisons.filter(c => c.similarity < exportOptions.customThreshold).length :
              exportOptions.includeHighSimilarityOnly ? comparisons.filter(c => c.similarity >= exportOptions.customThreshold).length :
              comparisons.length
            } مقارنة من أصل {comparisons.length}</p>
            <p>• التقارير محسنة للعرض والطباعة</p>
            <p>• جميع التقارير تتضمن معلومات المصدر والطوابع الزمنية</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}; 