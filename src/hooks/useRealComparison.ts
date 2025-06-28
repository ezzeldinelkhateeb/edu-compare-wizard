
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
    console.log('بدء عملية المقارنة:', { oldFiles: oldFiles.length, newFiles: newFiles.length, sessionName });
    
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
      // التحقق من وجود الملفات
      if (oldFiles.length === 0 || newFiles.length === 0) {
        throw new Error('يجب رفع ملفات من كلا الكتابين');
      }

      toast({
        title: "بدء المعالجة",
        description: "جاري إنشاء جلسة مقارنة جديدة..."
      });

      // إنشاء جلسة جديدة
      const sessionId = await realAIServices.createComparisonSession(sessionName);
      console.log('تم إنشاء الجلسة:', sessionId);
      
      setState(prev => ({ ...prev, sessionId, progress: 5 }));

      toast({
        title: "تم إنشاء الجلسة",
        description: "بدء معالجة الملفات باستخدام Landing.AI"
      });

      // معالجة الملفات باستخدام Landing.AI
      const { oldResults, newResults } = await realAIServices.processMultipleFiles(
        oldFiles,
        newFiles,
        sessionId,
        (progress, currentFile, fileType) => {
          console.log(`التقدم: ${progress}% - ${fileType}: ${currentFile}`);
          setState(prev => ({
            ...prev,
            progress: Math.min(progress, 70), // حجز 70% لمعالجة الملفات
            currentFile,
            currentFileType: fileType
          }));
        }
      );

      console.log('انتهت معالجة الملفات:', { oldResults: oldResults.length, newResults: newResults.length });

      setState(prev => ({
        ...prev,
        oldResults,
        newResults,
        progress: 75,
        currentFile: '',
        currentFileType: 'جاري المقارنة باستخدام Gemini AI...'
      }));

      toast({
        title: "انتهت معالجة الملفات",
        description: "بدء المقارنة الذكية باستخدام Gemini AI"
      });

      // إجراء المقارنة باستخدام Gemini
      const comparisons = await realAIServices.compareTexts(sessionId);
      console.log('انتهت المقارنة:', comparisons.length);

      setState(prev => ({
        ...prev,
        comparisons,
        isProcessing: false,
        progress: 100,
        currentFile: '',
        currentFileType: ''
      }));

      toast({
        title: "اكتملت المقارنة!",
        description: `تم تحليل ${comparisons.length} مقارنة بنجاح باستخدام الذكاء الاصطناعي`,
        duration: 5000
      });

    } catch (error) {
      console.error('خطأ في عملية المقارنة:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف في المعالجة';
      
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isProcessing: false,
        progress: 0,
        currentFile: '',
        currentFileType: ''
      }));

      toast({
        title: "فشل في المعالجة",
        description: errorMessage,
        variant: "destructive",
        duration: 8000
      });
    }
  }, [toast]);

  const exportHTMLReport = useCallback(async () => {
    if (!state.sessionId) {
      toast({
        title: "خطأ",
        description: "لا توجد جلسة نشطة للتصدير",
        variant: "destructive"
      });
      return;
    }

    try {
      toast({
        title: "جاري التصدير...",
        description: "تحضير تقرير HTML"
      });

      await realAIServices.exportHTMLReport(state.sessionId);
      
      toast({
        title: "تم تصدير التقرير بنجاح!",
        description: "تم تحميل تقرير HTML التفاعلي",
        duration: 5000
      });

    } catch (error) {
      console.error('فشل في تصدير HTML:', error);
      toast({
        title: "فشل في التصدير",
        description: error instanceof Error ? error.message : "خطأ في تصدير التقرير",
        variant: "destructive"
      });
    }
  }, [state.sessionId, toast]);

  const exportMarkdownReport = useCallback(async () => {
    if (!state.sessionId) {
      toast({
        title: "خطأ",
        description: "لا توجد جلسة نشطة للتصدير",
        variant: "destructive"
      });
      return;
    }

    try {
      toast({
        title: "جاري التصدير...",
        description: "تحضير التقرير الشامل"
      });

      await realAIServices.exportMarkdownReport(state.sessionId);
      
      toast({
        title: "تم تصدير التقرير الشامل!",
        description: "تم تحميل تقرير Markdown المفصل",
        duration: 5000
      });

    } catch (error) {
      console.error('فشل في تصدير Markdown:', error);
      toast({
        title: "فشل في التصدير",
        description: error instanceof Error ? error.message : "خطأ في تصدير التقرير",
        variant: "destructive"
      });
    }
  }, [state.sessionId, toast]);

  const resetState = useCallback(() => {
    setState({
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
  }, []);

  return {
    ...state,
    startComparison,
    exportHTMLReport,
    exportMarkdownReport,
    resetState
  };
};
