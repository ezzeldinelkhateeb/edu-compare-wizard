
import { useState, useCallback } from 'react';
import { realAIServices, ProcessingResult, ComparisonResult } from '@/services/realAIServices';
import { useToast } from '@/hooks/use-toast';

export interface RealComparisonState {
  isProcessing: boolean;
  progress: number;
  currentFile: string;
  currentFileType: string;
  sessionId: string | null;
  oldResults: ProcessingResult[];
  newResults: ProcessingResult[];
  comparisons: ComparisonResult[];
  error: string | null;
}

export const useRealComparison = () => {
  const [state, setState] = useState<RealComparisonState>({
    isProcessing: false,
    progress: 0,
    currentFile: '',
    currentFileType: '',
    sessionId: null,
    oldResults: [],
    newResults: [],
    comparisons: [],
    error: null
  });
  
  const { toast } = useToast();

  const startComparison = useCallback(async (oldFiles: File[], newFiles: File[], sessionName: string) => {
    setState(prev => ({
      ...prev,
      isProcessing: true,
      progress: 0,
      error: null,
      oldResults: [],
      newResults: [],
      comparisons: []
    }));

    try {
      // إنشاء جلسة جديدة
      const sessionId = await realAIServices.createComparisonSession(sessionName);
      setState(prev => ({ ...prev, sessionId }));

      toast({
        title: "بدء المعالجة",
        description: "تم إنشاء جلسة مقارنة جديدة"
      });

      // معالجة الملفات
      const { oldResults, newResults } = await realAIServices.processMultipleFiles(
        oldFiles,
        newFiles,
        sessionId,
        (progress, currentFile, fileType) => {
          setState(prev => ({
            ...prev,
            progress,
            currentFile,
            currentFileType: fileType
          }));
        }
      );

      setState(prev => ({
        ...prev,
        oldResults,
        newResults,
        progress: 75
      }));

      // إجراء المقارنات باستخدام Gemini
      const comparisons: ComparisonResult[] = [];
      const maxComparisons = Math.min(oldResults.length, newResults.length);

      for (let i = 0; i < maxComparisons; i++) {
        try {
          // جلب معرف المقارنة من قاعدة البيانات
          const comparisonResults = await realAIServices.getComparisonResults(sessionId);
          if (comparisonResults[i]) {
            const comparison = await realAIServices.compareTexts(sessionId, comparisonResults[i].id);
            comparisons.push(comparison);
          }
        } catch (error) {
          console.error(`خطأ في مقارنة الملف ${i + 1}:`, error);
        }
      }

      setState(prev => ({
        ...prev,
        comparisons,
        isProcessing: false,
        progress: 100
      }));

      toast({
        title: "اكتملت المقارنة",
        description: `تم مقارنة ${comparisons.length} ملف بنجاح باستخدام الذكاء الاصطناعي`
      });

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'خطأ غير معروف',
        isProcessing: false
      }));

      toast({
        title: "خطأ في المعالجة",
        description: "حدث خطأ أثناء معالجة الملفات",
        variant: "destructive"
      });
    }
  }, [toast]);

  const exportHTMLReport = useCallback(async () => {
    if (!state.sessionId) return;

    try {
      const htmlContent = await realAIServices.exportHTMLReport(state.sessionId);
      const blob = new Blob([htmlContent], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `تقرير_المقارنة_${new Date().toISOString().split('T')[0]}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: "تم تصدير التقرير",
        description: "تم تحميل تقرير HTML بنجاح"
      });

    } catch (error) {
      toast({
        title: "خطأ في التصدير",
        description: "فشل في تصدير التقرير",
        variant: "destructive"
      });
    }
  }, [state.sessionId, toast]);

  const exportMarkdownReport = useCallback(async () => {
    if (!state.sessionId) return;

    try {
      const mdContent = await realAIServices.exportMarkdownReport(state.sessionId);
      const blob = new Blob([mdContent], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `تقرير_المقارنة_الشامل_${new Date().toISOString().split('T')[0]}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: "تم تصدير التقرير الشامل",
        description: "تم تحميل تقرير Markdown بنجاح"
      });

    } catch (error) {
      toast({
        title: "خطأ في التصدير",
        description: "فشل في تصدير التقرير الشامل",
        variant: "destructive"
      });
    }
  }, [state.sessionId, toast]);

  return {
    ...state,
    startComparison,
    exportHTMLReport,
    exportMarkdownReport
  };
};
