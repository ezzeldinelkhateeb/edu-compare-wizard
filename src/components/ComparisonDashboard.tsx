import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRealComparison } from '@/hooks/useRealComparison';
import { useBatchComparison } from '@/hooks/useBatchComparison';
import { Badge } from '@/components/ui/badge';
import AdvancedReportDashboard from '@/components/AdvancedReportDashboard';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  ArrowLeft,
  AlertTriangle,
  RefreshCw,
  FolderOpen,
  Files,
  Download
} from 'lucide-react';
import { toast } from 'sonner';
import AdvancedComparisonDashboard from '@/components/AdvancedComparisonDashboard';
import { ProcessingResult, ComparisonResult } from '@/services/realAIServices';

interface ComparisonDashboardProps {
  files: {
    old: File[];
    new: File[];
  };
  onBack: () => void;
}

export function ComparisonDashboard({ files, onBack }: ComparisonDashboardProps) {
  const [processingMode, setProcessingMode] = useState<'single' | 'batch'>('single');
  
  const { 
    isLoading, 
    error, 
    progress,
    sessionId,
    oldImageResult,
    newImageResult,
    comparisonResult,
    visualComparisonResult,
    landingAIVerification,
    processingSteps,
    logs,
    startRealComparison,
    performVisualComparison,
    verifyLandingAI,
    forceLandingAI,
    resetComparison,
    downloadReport
  } = useRealComparison();

  const {
    isLoading: isBatchLoading,
    error: batchError,
    progress: batchProgress,
    sessionId: batchSessionId,
    batchResult,
    processingSteps: batchSteps,
    logs: batchLogs,
    currentFile,
    startBatchComparison,
    resetBatchComparison,
    downloadBatchReport
  } = useBatchComparison();

  const formatNumber = (value: number | undefined | null, decimals = 2) => {
    return typeof value === 'number' && !isNaN(value) ? value.toFixed(decimals) : 'N/A';
  };

  useEffect(() => {
    console.log('🚀 ComparisonDashboard: بدء تشغيل لوحة المقارنة');
    console.log('📁 الملفات المرفوعة:', { 
      oldFiles: files.old.length, 
      newFiles: files.new.length 
    });

    // تحديد نمط المعالجة
    const totalFiles = files.old.length + files.new.length;
    
    if (files.old.length === 1 && files.new.length === 1) {
      // معالجة ملف واحد
      setProcessingMode('single');
      console.log('🔄 بدء عملية المقارنة المفردة');
      startRealComparison(files.old[0], files.new[0]);
    } else if (totalFiles > 2) {
      // معالجة مجمعة
      setProcessingMode('batch');
      console.log('🔄 بدء المعالجة المجمعة للملفات المتعددة');
      toast.success(`تم اكتشاف ${totalFiles} ملف - سيتم استخدام المعالجة المجمعة`);
      startBatchComparison(files.old, files.new);
    } else {
      toast.error("يرجى رفع ملف واحد على الأقل في كل مجلد");
    }
  }, [files, startRealComparison, startBatchComparison]);

  const handleRetry = () => {
    if (processingMode === 'single' && files.old.length === 1 && files.new.length === 1) {
      resetComparison();
      setTimeout(() => {
        startRealComparison(files.old[0], files.new[0]);
      }, 500);
    } else if (processingMode === 'batch') {
      resetBatchComparison();
      setTimeout(() => {
        startBatchComparison(files.old, files.new);
      }, 500);
    }
  };

  // دالة للتحقق من Landing AI والمقارنة البصرية
  const handleAdvancedAnalysis = async () => {
    if (!sessionId) return;

    try {
      // التحقق من Landing AI
      const verification = await verifyLandingAI();
      console.log('🔍 تحقق Landing AI:', verification);

      // المقارنة البصرية
      const visualComparison = await performVisualComparison();
      console.log('🖼️ المقارنة البصرية:', visualComparison);

      console.log('✅ تم إجراء التحليل المتقدم بنجاح');
    } catch (error) {
      console.error('خطأ في التحليل المتقدم:', error);
    }
  };

  // دالة لإجبار استخدام Landing AI
  const handleForceLandingAI = async () => {
    if (!sessionId) return;

    try {
      const result = await forceLandingAI();
      console.log('🚀 نتيجة إجبار Landing AI:', result);
      console.log('✅ تم استخراج النص باستخدام Landing AI فقط');
    } catch (error) {
      console.error('خطأ في إجبار Landing AI:', error);
    }
  };

  if (isLoading || isBatchLoading) {
    const currentProgress = processingMode === 'batch' ? batchProgress : progress;
    const currentSteps = processingMode === 'batch' ? batchSteps : processingSteps;
    const currentLogs = processingMode === 'batch' ? batchLogs : logs;
    const modeTitle = processingMode === 'batch' ? 'المعالجة المجمعة' : 'معالجة المقارنة';
    const modeDescription = processingMode === 'batch' 
      ? `يتم الآن معالجة ${files.old.length + files.new.length} ملف باستخدام المعالجة المجمعة المتقدمة`
      : 'يتم الآن تحليل ومقارنة الملفات باستخدام خوارزميات الذكاء الاصطناعي';

    console.log(`⏳ معالجة: ${currentProgress}% (mode: ${processingMode}, batch: ${batchProgress}, single: ${progress})`);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header with back button */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              {onBack && (
                <Button variant="outline" onClick={onBack} disabled={isLoading || isBatchLoading}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة
                </Button>
              )}
              <div className="flex items-center gap-3">
                {processingMode === 'batch' ? <FolderOpen className="w-8 h-8 text-blue-600" /> : <Files className="w-8 h-8 text-blue-600" />}
                <h1 className="text-3xl font-bold text-gray-900">{modeTitle}</h1>
              </div>
            </div>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">جاري معالجة الملفات...</h2>
            <p className="text-lg text-gray-600">
              {modeDescription}
            </p>
            {processingMode === 'batch' && currentFile && (
              <p className="text-sm text-blue-600 mt-2">
                الملف الحالي: {currentFile}
              </p>
            )}
          </div>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>التقدم الإجمالي</span>
                <span>{Math.round(currentProgress)}%</span>
              </div>
              <Progress value={currentProgress} className="h-3" />
            </div>

            {/* عرض الخطوات */}
            <div className="space-y-3">
              {currentSteps.map((step, index) => (
                <div key={step.id} className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                    step.status === 'completed' ? 'bg-green-500' :
                    step.status === 'processing' ? 'bg-blue-500' :
                    step.status === 'error' ? 'bg-red-500' : 'bg-gray-300'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <span className="font-medium">{step.name}</span>
                    {step.status === 'processing' && (
                      <div className="text-sm text-blue-600">جاري المعالجة...</div>
                    )}
                    {step.duration && (
                      <div className="text-sm text-gray-500">({step.duration.toFixed(2)}s)</div>
                    )}
                    {step.details && (
                      <div className="text-sm text-gray-600">{step.details}</div>
                    )}
                  </div>
                  <Badge variant={step.status === 'completed' ? 'default' : 'secondary'}>
                    {step.status === 'completed' ? 'مكتمل' :
                     step.status === 'processing' ? 'جاري...' :
                     step.status === 'error' ? 'خطأ' : 'انتظار'}
                  </Badge>
                </div>
              ))}
            </div>

            {/* عرض آخر السجلات */}
            {currentLogs.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">سجل العمليات</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1 font-mono text-sm max-h-32 overflow-y-auto">
                    {currentLogs.slice(-5).map((log, index) => (
                      <div key={index} className="text-gray-700">{log}</div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </section>
    );
  }

  if (error || batchError) {
    const currentError = error || batchError;
    console.log('❌ خطأ في المقارنة:', currentError);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header with back button */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              {onBack && (
                <Button variant="outline" onClick={onBack}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة
                </Button>
              )}
              <h1 className="text-3xl font-bold text-gray-900">نتائج المقارنة</h1>
            </div>
          </div>

          <div className="text-center">
            <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-red-500" />
            <h2 className="text-2xl font-bold mb-2 text-red-600">
              حدث خطأ في {processingMode === 'batch' ? 'المعالجة المجمعة' : 'المقارنة'}
            </h2>
            <p className="text-lg text-gray-600 mb-6">{currentError}</p>
            
            <Alert className="mb-6 text-right">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>تعليمات لحل المشكلة:</AlertTitle>
              <AlertDescription>
                <ul className="text-sm space-y-1 mt-2">
                  <li>• تأكد من تشغيل الخادم الخلفي على http://localhost:8001</li>
                  <li>• تأكد من تشغيل Redis Server</li>
                  <li>• تأكد من تشغيل Celery Worker</li>
                  {processingMode === 'batch' && (
                    <li>• تأكد من أن جميع الملفات بصيغة مدعومة (JPG, PNG, PDF)</li>
                  )}
                  <li>• راجع ملف TROUBLESHOOTING.md للمساعدة التفصيلية</li>
                </ul>
              </AlertDescription>
            </Alert>
            
            <div className="flex gap-4 justify-center">
              <Button onClick={handleRetry} disabled={isLoading || isBatchLoading}>
                <RefreshCw className="w-4 h-4 mr-2" />
                المحاولة مرة أخرى
              </Button>
              {onBack && (
                <Button variant="outline" onClick={onBack}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة للرفع
                </Button>
              )}
            </div>
          </div>
        </div>
      </section>
    );
  }

  // إذا لا يوجد ملفات مناسبة للمقارنة
  if (files.old.length === 0 || files.new.length === 0) {
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold mb-2">لا توجد ملفات للمقارنة</h2>
          <p className="text-lg text-gray-600 mb-6">
            يرجى رفع ملف واحد على الأقل في كل من المجلدين (القديم والجديد)
          </p>
          {onBack && (
            <Button onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              العودة للرفع
            </Button>
          )}
        </div>
      </section>
    );
  }

  // عرض شاشة المعالجة البسيطة في وضع المعالجة المفردة فقط
  if (processingMode === 'single' && (isLoading || (!oldImageResult && !newImageResult && !comparisonResult && !error))) {
    console.log(`⏳ معالجة: ${progress}%`);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header with back button */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              {onBack && (
                <Button variant="outline" onClick={onBack} disabled={isLoading}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة
                </Button>
              )}
              <h1 className="text-3xl font-bold text-gray-900">معالجة المقارنة</h1>
            </div>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">جاري معالجة الملفات...</h2>
            <p className="text-lg text-gray-600">
              يتم الآن تحليل ومقارنة الملفات باستخدام خوارزميات الذكاء الاصطناعي
            </p>
          </div>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>التقدم الإجمالي</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-3" />
            </div>

            {/* عرض الخطوات */}
            <div className="space-y-3">
              {processingSteps.map((step, index) => (
                <div key={step.id} className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                    step.status === 'completed' ? 'bg-green-500' :
                    step.status === 'processing' ? 'bg-blue-500' :
                    step.status === 'error' ? 'bg-red-500' : 'bg-gray-300'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <span className="font-medium">{step.name}</span>
                    {step.status === 'processing' && (
                      <div className="text-sm text-blue-600">جاري المعالجة...</div>
                    )}
                    {step.duration && (
                      <div className="text-sm text-gray-500">({step.duration.toFixed(2)}s)</div>
                    )}
                  </div>
                  <Badge variant={step.status === 'completed' ? 'default' : 'secondary'}>
                    {step.status === 'completed' ? 'مكتمل' :
                     step.status === 'processing' ? 'جاري...' :
                     step.status === 'error' ? 'خطأ' : 'انتظار'}
                  </Badge>
                </div>
              ))}
            </div>

            {/* عرض آخر السجلات */}
            {logs.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">سجل العمليات</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1 font-mono text-sm max-h-32 overflow-y-auto">
                    {logs.slice(-5).map((log, index) => (
                      <div key={index} className="text-gray-700">{log}</div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </section>
    );
  }

  // عرض النتائج بناءً على نمط المعالجة
  if (processingMode === 'batch' && batchResult) {
    // تحويل نتائج المعالجة المجمعة إلى تنسيق متوافق مع AdvancedComparisonDashboard
    const mappedOldResults: ProcessingResult[] = batchResult.file_results?.map((result, index) => ({
      id: `old_${index}`,
      fileName: result.old_filename,
      extractedText: result.old_extracted_text || '', // النص المستخرج الفعلي
      confidence: result.confidence,
      fileUrl: '',
      jsonData: null,
      status: 'completed' as const
    })) || [];

    const mappedNewResults: ProcessingResult[] = batchResult.file_results?.map((result, index) => ({
      id: `new_${index}`,
      fileName: result.new_filename,
      extractedText: result.new_extracted_text || '', // النص المستخرج الفعلي
      confidence: result.confidence,
      fileUrl: '',
      jsonData: null,
      status: 'completed' as const
    })) || [];

    const mappedComparisons: ComparisonResult[] = batchResult.file_results?.map((result, index) => ({
      id: `comparison_${index}`,
      oldFileName: result.old_filename,
      newFileName: result.new_filename,
      similarity: result.similarity,
      analysis: {
        similarity_percentage: result.similarity,
        content_changes: [],
        questions_changes: [],
        examples_changes: [],
        major_differences: [],
        summary: result.summary || "حدث خطأ في التحليل المتقدم، يُنصح بالمراجعة اليدوية",
        recommendation: result.recommendation || "يُنصح بالمراجعة اليدوية للتأكد من التغييرات"
      },
      detailedReport: '',
      status: 'completed' as const
    })) || [];

    // دوال تحميل التقارير المحدثة
    const handleDownloadHTML = async () => {
      try {
        const response = await fetch(`/api/v1/advanced-processing/${batchSessionId}/download-html`);
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `تقرير_مقارنة_شامل_${batchSessionId}_${new Date().toISOString().slice(0, 19)}.html`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          toast.success('تم تحميل تقرير HTML بنجاح');
        } else {
          throw new Error('فشل في تحميل التقرير');
        }
      } catch (error) {
        console.error('خطأ في تحميل تقرير HTML:', error);
        toast.error('فشل في تحميل تقرير HTML');
      }
    };

    const handleDownloadMarkdown = async () => {
      try {
        const response = await fetch(`/api/v1/advanced-processing/${batchSessionId}/download-markdown`);
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `تقرير_مقارنة_شامل_${batchSessionId}_${new Date().toISOString().slice(0, 19)}.md`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          toast.success('تم تحميل تقرير Markdown بنجاح');
        } else {
          throw new Error('فشل في تحميل التقرير');
        }
      } catch (error) {
        console.error('خطأ في تحميل تقرير Markdown:', error);
        toast.error('فشل في تحميل تقرير Markdown');
      }
    };

    return (
      <AdvancedComparisonDashboard
        isProcessing={false}
        progress={100}
        currentFile=""
        currentFileType=""
        oldResults={mappedOldResults}
        newResults={mappedNewResults}
        comparisons={mappedComparisons}
        onExportHTML={handleDownloadHTML}
        onExportMarkdown={handleDownloadMarkdown}
        onBack={onBack}
      />
    );
  }

  // عرض التقرير المتقدم للمعالجة المفردة
  if (processingMode === 'single' && comparisonResult) {
    return (
      <AdvancedReportDashboard
        sessionId={sessionId || 'unknown'}
        oldImageResult={oldImageResult}
        newImageResult={newImageResult}
        comparisonResult={comparisonResult}
        isProcessing={isLoading}
        onRetry={handleRetry}
        onDownloadReport={downloadReport}
      />
    );
  }
}
