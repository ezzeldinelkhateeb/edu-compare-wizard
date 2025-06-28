
import { supabase } from '@/integrations/supabase/client';

export interface ProcessingResult {
  id: string;
  fileName: string;
  extractedText: string;
  confidence: number;
  fileUrl: string;
  jsonData: any;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

export interface ComparisonResult {
  id: string;
  oldFileName: string;
  newFileName: string;
  similarity: number;
  analysis: {
    similarity_percentage: number;
    content_changes: string[];
    questions_changes: string[];
    examples_changes: string[];
    major_differences: string[];
    summary: string;
    recommendation: string;
  };
  detailedReport: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

class RealAIServices {
  private static instance: RealAIServices;
  
  static getInstance(): RealAIServices {
    if (!RealAIServices.instance) {
      RealAIServices.instance = new RealAIServices();
    }
    return RealAIServices.instance;
  }

  // إنشاء جلسة مقارنة جديدة
  async createComparisonSession(sessionName: string): Promise<string> {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        throw new Error('المستخدم غير مسجل الدخول');
      }

      const { data, error } = await supabase
        .from('comparison_sessions')
        .insert({
          session_name: sessionName,
          user_id: user.id,
          status: 'pending'
        })
        .select()
        .single();

      if (error) {
        console.error('خطأ في إنشاء الجلسة:', error);
        throw error;
      }
      
      console.log('تم إنشاء جلسة جديدة:', data.id);
      return data.id;
    } catch (error) {
      console.error('فشل في إنشاء جلسة المقارنة:', error);
      throw error;
    }
  }

  // معالجة صورة واحدة باستخدام Landing.AI
  async processImage(
    imageFile: File, 
    sessionId: string, 
    fileType: 'old' | 'new',
    onProgress?: (progress: number) => void
  ): Promise<ProcessingResult> {
    try {
      console.log(`بدء معالجة ${fileType} ملف: ${imageFile.name}`);
      onProgress?.(10);

      const formData = new FormData();
      formData.append('image', imageFile);
      formData.append('sessionId', sessionId);
      formData.append('fileName', imageFile.name);
      formData.append('fileType', fileType);

      onProgress?.(30);

      const { data, error } = await supabase.functions.invoke('process-image', {
        body: formData
      });

      if (error) {
        console.error('خطأ في استدعاء دالة معالجة الصورة:', error);
        throw new Error(`فشل في معالجة الصورة: ${error.message}`);
      }

      if (!data || !data.success) {
        console.error('استجابة غير صحيحة من دالة معالجة الصورة:', data);
        throw new Error('فشل في معالجة الصورة - استجابة غير صحيحة');
      }

      onProgress?.(100);

      const result: ProcessingResult = {
        id: crypto.randomUUID(),
        fileName: imageFile.name,
        extractedText: data.extractedText || '',
        confidence: data.confidence || 0,
        fileUrl: data.fileUrl || '',
        jsonData: data.jsonData || null,
        status: 'completed'
      };

      console.log('تم معالجة الملف بنجاح:', result);
      return result;

    } catch (error) {
      console.error(`خطأ في معالجة ${fileType} ملف ${imageFile.name}:`, error);
      return {
        id: crypto.randomUUID(),
        fileName: imageFile.name,
        extractedText: '',
        confidence: 0,
        fileUrl: '',
        jsonData: null,
        status: 'error'
      };
    }
  }

  // معالجة متعددة الملفات
  async processMultipleFiles(
    oldFiles: File[],
    newFiles: File[],
    sessionId: string,
    onProgress: (progress: number, currentFile: string, fileType: string) => void
  ): Promise<{ oldResults: ProcessingResult[], newResults: ProcessingResult[] }> {
    
    const oldResults: ProcessingResult[] = [];
    const newResults: ProcessingResult[] = [];
    
    const totalFiles = oldFiles.length + newFiles.length;
    let processedFiles = 0;

    console.log(`بدء معالجة ${totalFiles} ملف`);

    // معالجة الملفات القديمة
    for (const file of oldFiles) {
      const currentProgress = (processedFiles / totalFiles) * 50;
      onProgress(currentProgress, file.name, 'الكتاب القديم');
      
      const result = await this.processImage(file, sessionId, 'old');
      oldResults.push(result);
      processedFiles++;
    }

    // معالجة الملفات الجديدة
    for (const file of newFiles) {
      const currentProgress = 50 + (processedFiles / totalFiles) * 50;
      onProgress(currentProgress, file.name, 'الكتاب الجديد');
      
      const result = await this.processImage(file, sessionId, 'new');
      newResults.push(result);
      processedFiles++;
    }

    console.log('انتهت معالجة جميع الملفات');
    return { oldResults, newResults };
  }

  // مقارنة النصوص باستخدام Gemini
  async compareTexts(sessionId: string): Promise<ComparisonResult[]> {
    try {
      console.log('بدء مقارنة النصوص للجلسة:', sessionId);

      // جلب المقارنات من قاعدة البيانات
      const { data: comparisons, error } = await supabase
        .from('file_comparisons')
        .select('*')
        .eq('session_id', sessionId);

      if (error) {
        console.error('خطأ في جلب المقارنات:', error);
        throw error;
      }

      if (!comparisons || comparisons.length === 0) {
        console.log('لا توجد مقارنات للمعالجة');
        return [];
      }

      const results: ComparisonResult[] = [];

      // معالجة كل مقارنة باستخدام Gemini
      for (const comparison of comparisons) {
        try {
          console.log('معالجة المقارنة:', comparison.id);

          const { data, error: compareError } = await supabase.functions.invoke('compare-texts', {
            body: { 
              sessionId: sessionId, 
              comparisonId: comparison.id 
            }
          });

          if (compareError) {
            console.error('خطأ في مقارنة النصوص:', compareError);
            continue;
          }

          if (data && data.success && data.analysis) {
            const result: ComparisonResult = {
              id: comparison.id,
              oldFileName: comparison.old_file_name,
              newFileName: comparison.new_file_name,
              similarity: data.analysis.similarity_percentage || 0,
              analysis: {
                similarity_percentage: data.analysis.similarity_percentage || 0,
                content_changes: data.analysis.content_changes || [],
                questions_changes: data.analysis.questions_changes || [],
                examples_changes: data.analysis.examples_changes || [],
                major_differences: data.analysis.major_differences || [],
                summary: data.analysis.summary || '',
                recommendation: data.analysis.recommendation || ''
              },
              detailedReport: data.detailedReport || '',
              status: 'completed'
            };

            results.push(result);
            console.log('تمت المقارنة بنجاح:', result);
          }

        } catch (error) {
          console.error(`خطأ في معالجة المقارنة ${comparison.id}:`, error);
        }
      }

      return results;

    } catch (error) {
      console.error('فشل في مقارنة النصوص:', error);
      throw error;
    }
  }

  // جلب نتائج المقارنة المحدثة
  async getComparisonResults(sessionId: string): Promise<ComparisonResult[]> {
    try {
      const { data, error } = await supabase
        .from('file_comparisons')
        .select('*')
        .eq('session_id', sessionId)
        .eq('status', 'completed');

      if (error) {
        console.error('خطأ في جلب النتائج:', error);
        throw error;
      }

      return (data || []).map(item => {
        const defaultAnalysis = {
          similarity_percentage: item.text_similarity || 0,
          content_changes: [],
          questions_changes: [],
          examples_changes: [],
          major_differences: [],
          summary: '',
          recommendation: ''
        };

        let parsedAnalysis = defaultAnalysis;
        if (typeof item.changes_detected === 'string') {
          try {
            const parsed = JSON.parse(item.changes_detected);
            parsedAnalysis = { ...defaultAnalysis, ...parsed };
          } catch (e) {
            console.error('خطأ في تحليل البيانات:', e);
          }
        } else if (item.changes_detected && typeof item.changes_detected === 'object') {
          parsedAnalysis = { ...defaultAnalysis, ...item.changes_detected };
        }

        return {
          id: item.id,
          oldFileName: item.old_file_name,
          newFileName: item.new_file_name,
          similarity: item.text_similarity || 0,
          analysis: parsedAnalysis,
          detailedReport: '',
          status: 'completed' as const
        };
      });
    } catch (error) {
      console.error('فشل في جلب النتائج:', error);
      return [];
    }
  }

  // تصدير تقرير HTML محسن
  async exportHTMLReport(sessionId: string): Promise<void> {
    try {
      const results = await this.getComparisonResults(sessionId);
      
      if (results.length === 0) {
        throw new Error('لا توجد نتائج للتصدير');
      }

      const htmlContent = this.generateEnhancedHTMLReport(results);
      this.downloadFile(htmlContent, `تقرير_المقارنة_${new Date().toISOString().split('T')[0]}.html`, 'text/html');
      
    } catch (error) {
      console.error('فشل في تصدير تقرير HTML:', error);
      throw error;
    }
  }

  // تصدير تقرير Markdown شامل
  async exportMarkdownReport(sessionId: string): Promise<void> {
    try {
      const results = await this.getComparisonResults(sessionId);
      
      if (results.length === 0) {
        throw new Error('لا توجد نتائج للتصدير');
      }

      const mdContent = this.generateEnhancedMarkdownReport(results);
      this.downloadFile(mdContent, `تقرير_المقارنة_الشامل_${new Date().toISOString().split('T')[0]}.md`, 'text/markdown');
      
    } catch (error) {
      console.error('فشل في تصدير تقرير Markdown:', error);
      throw error;
    }
  }

  private generateEnhancedHTMLReport(results: ComparisonResult[]): string {
    const totalSimilarity = results.reduce((sum, r) => sum + r.similarity, 0);
    const avgSimilarity = results.length > 0 ? totalSimilarity / results.length : 0;

    return `<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير مقارنة المناهج التعليمية</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', 'Arial', sans-serif; 
            margin: 0; padding: 20px; 
            line-height: 1.6; 
            color: #333; 
            background: #f5f5f5;
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 3px solid #3b82f6; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { color: #1f2937; margin: 0; font-size: 2.5rem; }
        .header p { color: #6b7280; font-size: 1.1rem; margin: 10px 0 0 0; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .summary-card { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 25px; border-radius: 10px; text-align: center; }
        .summary-number { font-size: 3rem; font-weight: bold; margin: 0; }
        .summary-label { font-size: 1.1rem; margin: 5px 0 0 0; opacity: 0.9; }
        .comparison { background: #f9fafb; margin: 25px 0; padding: 25px; border-radius: 10px; border-right: 5px solid #3b82f6; }
        .comparison h3 { color: #1f2937; margin: 0 0 15px 0; font-size: 1.5rem; }
        .similarity-bar { background: #e5e7eb; height: 20px; border-radius: 10px; overflow: hidden; margin: 15px 0; }
        .similarity-fill { height: 100%; background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981); border-radius: 10px; transition: width 0.3s ease; }
        .changes-section { margin: 20px 0; }
        .changes-title { color: #374151; font-weight: 600; margin: 15px 0 10px 0; font-size: 1.1rem; }
        .changes-list { background: white; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; }
        .changes-list li { margin: 8px 0; padding: 5px 0; }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; }
        @media print { body { background: white; } .container { box-shadow: none; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>تقرير مقارنة المناهج التعليمية</h1>
            <p>تم إنشاؤه في: ${new Date().toLocaleString('ar-EG')} | باستخدام الذكاء الاصطناعي</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-number">${results.length}</div>
                <div class="summary-label">إجمالي المقارنات</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">${Math.round(avgSimilarity)}%</div>
                <div class="summary-label">متوسط التطابق</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">${results.filter(r => r.similarity > 80).length}</div>
                <div class="summary-label">مقارنات عالية التطابق</div>
            </div>
        </div>

        ${results.map((result, index) => `
            <div class="comparison">
                <h3>مقارنة ${index + 1}: ${result.oldFileName} ↔ ${result.newFileName}</h3>
                
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: ${result.similarity}%"></div>
                </div>
                <p style="text-align: center; font-weight: bold; color: #3b82f6; font-size: 1.2rem;">
                    نسبة التطابق: ${result.similarity}%
                </p>

                <div class="changes-section">
                    <div class="changes-title">🔄 التغييرات في المحتوى:</div>
                    <div class="changes-list">
                        <ul>
                            ${result.analysis.content_changes?.length > 0 
                                ? result.analysis.content_changes.map(change => `<li>${change}</li>`).join('') 
                                : '<li>لا توجد تغييرات في المحتوى</li>'}
                        </ul>
                    </div>
                </div>

                <div class="changes-section">
                    <div class="changes-title">❓ التغييرات في الأسئلة:</div>
                    <div class="changes-list">
                        <ul>
                            ${result.analysis.questions_changes?.length > 0 
                                ? result.analysis.questions_changes.map(change => `<li>${change}</li>`).join('') 
                                : '<li>لا توجد تغييرات في الأسئلة</li>'}
                        </ul>
                    </div>
                </div>

                <div class="changes-section">
                    <div class="changes-title">📋 ملخص التحليل:</div>
                    <div class="changes-list">
                        <p>${result.analysis.summary || 'غير متوفر'}</p>
                    </div>
                </div>

                <div class="changes-section">
                    <div class="changes-title">💡 التوصيات:</div>
                    <div class="changes-list">
                        <p>${result.analysis.recommendation || 'لا توجد توصيات'}</p>
                    </div>
                </div>
            </div>
        `).join('')}

        <div class="footer">
            <p>تم إنشاء هذا التقرير بواسطة نظام مقارن المناهج التعليمية باستخدام الذكاء الاصطناعي</p>
            <p>Landing.AI للتعرف البصري | Google Gemini للتحليل الذكي</p>
        </div>
    </div>
</body>
</html>`;
  }

  private generateEnhancedMarkdownReport(results: ComparisonResult[]): string {
    const totalSimilarity = results.reduce((sum, r) => sum + r.similarity, 0);
    const avgSimilarity = results.length > 0 ? totalSimilarity / results.length : 0;

    return `# تقرير مقارنة المناهج التعليمية الشامل

**📅 تاريخ التقرير**: ${new Date().toLocaleString('ar-EG')}  
**🤖 تم إنشاؤه بواسطة**: الذكاء الاصطناعي (Landing.AI + Google Gemini)

---

## 📊 الملخص التنفيذي

| المؤشر | القيمة |
|---------|--------|
| إجمالي المقارنات | ${results.length} |
| متوسط التطابق | ${Math.round(avgSimilarity)}% |
| مقارنات عالية التطابق (>80%) | ${results.filter(r => r.similarity > 80).length} |
| مقارنات منخفضة التطابق (<60%) | ${results.filter(r => r.similarity < 60).length} |

---

${results.map((result, index) => `
## 📝 مقارنة ${index + 1}: ${result.oldFileName} ↔ ${result.newFileName}

### 📈 نسبة التطابق: ${result.similarity}%

### 🔄 التغييرات في المحتوى:
${result.analysis.content_changes?.length > 0 
  ? result.analysis.content_changes.map(change => `- ${change}`).join('\n') 
  : '- لا توجد تغييرات في المحتوى'}

### ❓ التغييرات في الأسئلة:
${result.analysis.questions_changes?.length > 0 
  ? result.analysis.questions_changes.map(change => `- ${change}`).join('\n') 
  : '- لا توجد تغييرات في الأسئلة'}

### 📚 التغييرات في الأمثلة:
${result.analysis.examples_changes?.length > 0 
  ? result.analysis.examples_changes.map(change => `- ${change}`).join('\n') 
  : '- لا توجد تغييرات في الأمثلة'}

### 🎯 الاختلافات الرئيسية:
${result.analysis.major_differences?.length > 0 
  ? result.analysis.major_differences.map(diff => `- ${diff}`).join('\n') 
  : '- لا توجد اختلافات رئيسية'}

### 📋 ملخص التحليل:
${result.analysis.summary || 'غير متوفر'}

### 💡 التوصيات:
${result.analysis.recommendation || 'لا توجد توصيات'}

---
`).join('')}

## 🔍 تحليل شامل للنتائج

### التوزيع حسب نسبة التطابق:
- **عالي التطابق (80-100%)**: ${results.filter(r => r.similarity >= 80).length} مقارنة
- **متوسط التطابق (60-79%)**: ${results.filter(r => r.similarity >= 60 && r.similarity < 80).length} مقارنة  
- **منخفض التطابق (أقل من 60%)**: ${results.filter(r => r.similarity < 60).length} مقارنة

### أهم الملاحظات:
- المحتوى الذي تغير بشكل كبير يحتاج إلى مراجعة دقيقة
- الأسئلة الجديدة تتطلب تحديث خطة التدريس
- التوصيات المقترحة تساعد في التكيف مع التغييرات

---

**📝 ملاحظة**: تم إنشاء هذا التقرير باستخدام تقنيات الذكاء الاصطناعي المتقدمة لضمان دقة التحليل والمقارنة.`;
  }

  private downloadFile(content: string, fileName: string, mimeType: string): void {
    try {
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      console.log('تم تحميل الملف بنجاح:', fileName);
    } catch (error) {
      console.error('فشل في تحميل الملف:', error);
      throw error;
    }
  }
}

export const realAIServices = RealAIServices.getInstance();
