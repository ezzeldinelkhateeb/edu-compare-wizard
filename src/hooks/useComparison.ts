
import { useState, useCallback } from 'react';
import { aiProcessingService, ProcessingResult } from '@/services/aiServices';
import { reportService, ReportData } from '@/services/reportService';
import { useToast } from '@/hooks/use-toast';

export interface ComparisonState {
  isProcessing: boolean;
  progress: number;
  currentFile: string;
  results: ProcessingResult[];
  error: string | null;
}

export const useComparison = () => {
  const [state, setState] = useState<ComparisonState>({
    isProcessing: false,
    progress: 0,
    currentFile: '',
    results: [],
    error: null
  });
  
  const { toast } = useToast();

  const startComparison = useCallback(async (oldFiles: File[], newFiles: File[]) => {
    setState(prev => ({
      ...prev,
      isProcessing: true,
      progress: 0,
      error: null,
      results: []
    }));

    try {
      const results = await aiProcessingService.processFiles(
        oldFiles,
        newFiles,
        (progress, currentFile) => {
          setState(prev => ({
            ...prev,
            progress,
            currentFile
          }));
        }
      );

      setState(prev => ({
        ...prev,
        results,
        isProcessing: false,
        progress: 100
      }));

      toast({
        title: "تم الانتهاء من المقارنة",
        description: `تم مقارنة ${results.length} ملف بنجاح`
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

  const exportPDFReport = useCallback(async () => {
    if (state.results.length === 0) return;

    try {
      const reportData: ReportData = {
        totalFiles: state.results.length,
        identicalFiles: state.results.filter(r => r.textSimilarity > 95 && r.visualSimilarity > 95).length,
        changedFiles: state.results.filter(r => r.textSimilarity <= 95 || r.visualSimilarity <= 95).length,
        averageSimilarity: state.results.reduce((acc, r) => acc + (r.textSimilarity + r.visualSimilarity) / 2, 0) / state.results.length,
        processingTime: state.results.reduce((acc, r) => acc + r.processingTime, 0),
        detailedResults: state.results.map((result, index) => ({
          fileName: `ملف ${index + 1}`,
          visualSimilarity: result.visualSimilarity,
          textSimilarity: result.textSimilarity,
          overallScore: Math.round((result.visualSimilarity + result.textSimilarity) / 2),
          changes: result.changes,
          status: result.textSimilarity > 95 && result.visualSimilarity > 95 ? 'identical' : 'changed'
        }))
      };

      const blob = await reportService.generatePDFReport(reportData);
      reportService.downloadFile(blob, `تقرير_المقارنة_${new Date().toISOString().split('T')[0]}.html`);
      
      toast({
        title: "تم تصدير التقرير",
        description: "تم تحميل التقرير بنجاح"
      });

    } catch (error) {
      toast({
        title: "خطأ في التصدير",
        description: "فشل في تصدير التقرير",
        variant: "destructive"
      });
    }
  }, [state.results, toast]);

  const exportPowerPointReport = useCallback(async () => {
    if (state.results.length === 0) return;

    try {
      const reportData: ReportData = {
        totalFiles: state.results.length,
        identicalFiles: state.results.filter(r => r.textSimilarity > 95 && r.visualSimilarity > 95).length,
        changedFiles: state.results.filter(r => r.textSimilarity <= 95 || r.visualSimilarity <= 95).length,
        averageSimilarity: state.results.reduce((acc, r) => acc + (r.textSimilarity + r.visualSimilarity) / 2, 0) / state.results.length,
        processingTime: state.results.reduce((acc, r) => acc + r.processingTime, 0),
        detailedResults: []
      };

      const blob = await reportService.generatePowerPointReport(reportData);
      reportService.downloadFile(blob, `عرض_المقارنة_${new Date().toISOString().split('T')[0]}.pptx`);
      
      toast({
        title: "تم تصدير العرض التقديمي",
        description: "تم تحميل ملف PowerPoint بنجاح"
      });

    } catch (error) {
      toast({
        title: "خطأ في التصدير",
        description: "فشل في تصدير العرض التقديمي",
        variant: "destructive"
      });
    }
  }, [state.results, toast]);

  return {
    ...state,
    startComparison,
    exportPDFReport,
    exportPowerPointReport
  };
};
