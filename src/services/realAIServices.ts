
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
    const { data: { user } } = await supabase.auth.getUser();
    
    const { data, error } = await supabase
      .from('comparison_sessions')
      .insert({
        session_name: sessionName,
        user_id: user?.id,
        status: 'pending'
      })
      .select()
      .single();

    if (error) throw error;
    return data.id;
  }

  // معالجة صورة واحدة باستخدام Landing.AI
  async processImage(
    imageFile: File, 
    sessionId: string, 
    fileType: 'old' | 'new',
    onProgress?: (progress: number) => void
  ): Promise<ProcessingResult> {
    
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('sessionId', sessionId);
    formData.append('fileName', imageFile.name);
    formData.append('fileType', fileType);

    onProgress?.(20);

    const { data, error } = await supabase.functions.invoke('process-image', {
      body: formData
    });

    if (error) throw error;

    onProgress?.(100);

    return {
      id: crypto.randomUUID(),
      fileName: imageFile.name,
      extractedText: data.extractedText,
      confidence: data.confidence,
      fileUrl: data.fileUrl,
      jsonData: data.jsonData,
      status: 'completed'
    };
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

    // معالجة الملفات القديمة
    for (const file of oldFiles) {
      onProgress(
        (processedFiles / totalFiles) * 50, 
        file.name, 
        'الكتاب القديم'
      );
      
      try {
        const result = await this.processImage(file, sessionId, 'old');
        oldResults.push(result);
      } catch (error) {
        console.error(`خطأ في معالجة ${file.name}:`, error);
        oldResults.push({
          id: crypto.randomUUID(),
          fileName: file.name,
          extractedText: '',
          confidence: 0,
          fileUrl: '',
          jsonData: null,
          status: 'error'
        });
      }
      
      processedFiles++;
    }

    // معالجة الملفات الجديدة
    for (const file of newFiles) {
      onProgress(
        50 + (processedFiles / totalFiles) * 50, 
        file.name, 
        'الكتاب الجديد'
      );
      
      try {
        const result = await this.processImage(file, sessionId, 'new');
        newResults.push(result);
      } catch (error) {
        console.error(`خطأ في معالجة ${file.name}:`, error);
        newResults.push({
          id: crypto.randomUUID(),
          fileName: file.name,
          extractedText: '',
          confidence: 0,
          fileUrl: '',
          jsonData: null,
          status: 'error'
        });
      }
      
      processedFiles++;
    }

    return { oldResults, newResults };
  }

  // مقارنة النصوص باستخدام Gemini
  async compareTexts(sessionId: string, comparisonId: string): Promise<ComparisonResult> {
    const { data, error } = await supabase.functions.invoke('compare-texts', {
      body: { sessionId, comparisonId }
    });

    if (error) throw error;

    return {
      id: comparisonId,
      oldFileName: '',
      newFileName: '',
      similarity: data.analysis.similarity_percentage,
      analysis: data.analysis,
      detailedReport: data.detailedReport,
      status: 'completed'
    };
  }

  // جلب نتائج المقارنة
  async getComparisonResults(sessionId: string): Promise<ComparisonResult[]> {
    const { data, error } = await supabase
      .from('file_comparisons')
      .select('*')
      .eq('session_id', sessionId)
      .eq('status', 'completed');

    if (error) throw error;

    return data.map(item => {
      // Create default analysis structure
      const defaultAnalysis = {
        similarity_percentage: item.text_similarity || 0,
        content_changes: [],
        questions_changes: [],
        examples_changes: [],
        major_differences: [],
        summary: '',
        recommendation: ''
      };

      // Parse changes_detected safely
      let parsedAnalysis = defaultAnalysis;
      if (typeof item.changes_detected === 'string') {
        try {
          const parsed = JSON.parse(item.changes_detected);
          parsedAnalysis = { ...defaultAnalysis, ...parsed };
        } catch (e) {
          console.error('Error parsing changes_detected:', e);
        }
      } else if (item.changes_detected && typeof item.changes_detected === 'object') {
        parsedAnalysis = { ...defaultAnalysis, ...item.changes_detected };
      }

      return {
        id: item.id,
        oldFileName: item.old_file_name,
        newFileName: item.new_file_name,
        similarity: item.text_similarity,
        analysis: parsedAnalysis,
        detailedReport: '',
        status: 'completed' as const
      };
    });
  }

  // تصدير تقرير HTML
  async exportHTMLReport(sessionId: string): Promise<string> {
    const results = await this.getComparisonResults(sessionId);
    
    const htmlContent = `
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير مقارنة المناهج</title>
    <style>
        body { font-family: 'Arial', sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 40px; }
        .comparison { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .changes { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .similarity { font-size: 1.2em; font-weight: bold; color: #2563eb; }
        ul { padding-right: 20px; }
        li { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>تقرير مقارنة المناهج الدراسية</h1>
        <p>تاريخ التقرير: ${new Date().toLocaleString('ar-EG')}</p>
    </div>
    
    ${results.map(result => `
        <div class="comparison">
            <h2>مقارنة: ${result.oldFileName} ↔ ${result.newFileName}</h2>
            <div class="similarity">نسبة التطابق: ${result.similarity}%</div>
            
            <div class="changes">
                <h3>التغييرات في المحتوى:</h3>
                <ul>
                    ${result.analysis.content_changes?.map(change => `<li>${change}</li>`).join('') || '<li>لا توجد تغييرات</li>'}
                </ul>
            </div>
            
            <div class="changes">
                <h3>التغييرات في الأسئلة:</h3>
                <ul>
                    ${result.analysis.questions_changes?.map(change => `<li>${change}</li>`).join('') || '<li>لا توجد تغييرات</li>'}
                </ul>
            </div>
            
            <div class="changes">
                <h3>ملخص التحليل:</h3>
                <p>${result.analysis.summary || 'غير متوفر'}</p>
            </div>
        </div>
    `).join('')}
    
</body>
</html>`;

    return htmlContent;
  }

  // تصدير تقرير Markdown
  async exportMarkdownReport(sessionId: string): Promise<string> {
    const results = await this.getComparisonResults(sessionId);
    
    let mdContent = `# تقرير مقارنة المناهج الدراسية الشامل

**تاريخ التقرير**: ${new Date().toLocaleString('ar-EG')}

---

`;

    for (const result of results) {
      mdContent += `## مقارنة: ${result.oldFileName} ↔ ${result.newFileName}

### نسبة التطابق: ${result.similarity}%

### التغييرات في المحتوى:
${result.analysis.content_changes?.map(change => `- ${change}`).join('\n') || '- لا توجد تغييرات'}

### التغييرات في الأسئلة:
${result.analysis.questions_changes?.map(change => `- ${change}`).join('\n') || '- لا توجد تغييرات'}

### التغييرات في الأمثلة:
${result.analysis.examples_changes?.map(change => `- ${change}`).join('\n') || '- لا توجد تغييرات'}

### الاختلافات الرئيسية:
${result.analysis.major_differences?.map(diff => `- ${diff}`).join('\n') || '- لا توجد اختلافات رئيسية'}

### ملخص التحليل:
${result.analysis.summary || 'غير متوفر'}

### التوصيات:
${result.analysis.recommendation || 'لا توجد توصيات'}

---

`;
    }

    return mdContent;
  }
}

export const realAIServices = RealAIServices.getInstance();
