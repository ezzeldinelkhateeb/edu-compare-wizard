import { useState, useCallback, useRef } from 'react';
import React from 'react';
import { toast } from 'sonner';

interface BatchProcessingStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  duration?: number;
  details?: string;
}

interface BatchFileResult {
  old_filename: string;
  new_filename: string;
  similarity: number;
  confidence: number;
  processing_time: number;
  summary?: string;
  recommendation?: string;
  changes?: Record<string, unknown>;
  old_extracted_text?: string;
  new_extracted_text?: string;
}

interface BatchComparisonResult {
  session_id: string;
  total_files: number;
  processed_files: number;
  successful_comparisons: number;
  failed_comparisons: number;
  average_similarity: number;
  total_processing_time: number;
  file_results: BatchFileResult[];
  summary_report: string;
}

interface BatchComparisonState {
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  batchResult: BatchComparisonResult | null;
  processingSteps: BatchProcessingStep[];
  logs: string[];
  progress: number;
  currentFile: string | null;
}

const initialSteps: BatchProcessingStep[] = [
  { id: 'session', name: 'إنشاء جلسة المعالجة المجمعة', status: 'pending', progress: 0 },
  { id: 'upload', name: 'رفع الملفات', status: 'pending', progress: 0 },
  { id: 'processing', name: 'معالجة الملفات', status: 'pending', progress: 0 },
  { id: 'comparison', name: 'مقارنة المحتوى', status: 'pending', progress: 0 },
  { id: 'report', name: 'إنشاء التقرير الشامل', status: 'pending', progress: 0 }
];

const API_PREFIX = '/api/v1';

async function fetchWithFallback(path: string, options?: RequestInit): Promise<Response> {
  const url = path;
  
  console.log(`🔗 محاولة الاتصال بـ: ${url}`);
  
  try {
    const response = await fetch(url, options);
    console.log(`📡 استجابة الخادم: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ message: 'Could not parse error body' }));
      console.error(`⚠️ HTTP error! status: ${response.status}`, errorBody);
      throw new Error(`Request to ${url} failed with status ${response.status}: ${errorBody.detail || response.statusText}`);
    }
    return response;
  } catch (err) {
    console.error(`⚠️ فشل الاتصال بـ ${url}:`, err);
    throw err;
  }
}

export const useBatchComparison = () => {
  const [state, setState] = useState<BatchComparisonState>({
    isLoading: false,
    error: null,
    sessionId: null,
    batchResult: null,
    processingSteps: [...initialSteps],
    logs: [],
    progress: 0,
    currentFile: null
  });

  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const apiFetch = useCallback(
    async (path: string, options?: RequestInit) => {
      const cleanPath = path.startsWith('/api/v1') ? path.substring(7) : path;
      const correctedPath = cleanPath.startsWith('/') ? `${API_PREFIX}${cleanPath}` : `${API_PREFIX}/${cleanPath}`;
      return fetchWithFallback(correctedPath, options);
    },
    []
  );

  // دالة للتقدم المرئي التدريجي
  const startVisualProgress = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    progressIntervalRef.current = setInterval(() => {
      setState(prev => {
        // إذا كانت المعالجة قيد التقدم ولم تصل للنهاية
        if (prev.isLoading && prev.progress < 85) {
          const increment = Math.random() * 2 + 0.5; // زيادة عشوائية بين 0.5-2.5%
          const newProgress = Math.min(prev.progress + increment, 85);
          console.log(`🎯 تقدم مرئي: ${newProgress.toFixed(1)}%`);
          return { ...prev, progress: newProgress };
        }
        return prev;
      });
    }, 3000); // كل 3 ثوان
  }, []);

  const stopVisualProgress = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
  }, []);

  const addLog = useCallback((message: string, level: 'info' | 'error' | 'success' = 'info') => {
    const timestamp = new Date().toLocaleTimeString('ar-SA');
    const logEntry = `[${timestamp}] ${message}`;
    
    console.log(`🔍 ${logEntry}`);
    
    setState(prev => ({
      ...prev,
      logs: [...prev.logs.slice(-50), logEntry] // Keep last 50 logs
    }));
  }, []);

  const updateStep = useCallback((stepId: string, updates: Partial<BatchProcessingStep>) => {
    setState(prev => ({
      ...prev,
      processingSteps: prev.processingSteps.map(step =>
        step.id === stepId ? { ...step, ...updates } : step
      )
    }));
  }, []);

  const calculateProgress = useCallback(() => {
    setState(prev => {
      const completedSteps = prev.processingSteps.filter(step => step.status === 'completed').length;
      const totalSteps = prev.processingSteps.length;
      const newProgress = (completedSteps / totalSteps) * 100;
      
      return {
        ...prev,
        progress: newProgress
      };
    });
  }, []);

  const startBatchComparison = useCallback(async (oldFiles: File[], newFiles: File[]) => {
    try {
      setState(prev => ({
        ...prev,
        isLoading: true,
        error: null,
        batchResult: null,
        processingSteps: [...initialSteps],
        logs: [],
        progress: 0,
        currentFile: null
      }));

      addLog(`🚀 بدء المعالجة المجمعة: ${oldFiles.length} ملف قديم، ${newFiles.length} ملف جديد`);
      
      // تحديث تقدم فوري لإظهار النشاط
      setTimeout(() => setState(prev => ({ ...prev, progress: 5 })), 100);
      
      // بدء التقدم المرئي
      startVisualProgress();
      
      // Step 1: Create processing session
      updateStep('session', { status: 'processing', progress: 20 });
      addLog('📝 إنشاء جلسة معالجة متقدمة...');
      
      const sessionResponse = await apiFetch('/advanced-processing/create-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_name: `batch_comparison_${new Date().toISOString().slice(0, 19)}`,
          processing_type: 'batch_comparison'
        })
      });

      const sessionData = await sessionResponse.json();
      const sessionId = sessionData.session_id;
      
      setState(prev => ({ ...prev, sessionId }));
      updateStep('session', { status: 'completed', progress: 100 });
      addLog(`✅ تم إنشاء الجلسة: ${sessionId}`);
      
      // تحديث التقدم بعد إنشاء الجلسة
      setState(prev => ({ ...prev, progress: 10 }));

      // Step 2: Upload files
      updateStep('upload', { status: 'processing', progress: 30 });
      addLog('📤 رفع الملفات إلى الخادم...');

      const formData = new FormData();
      
      // Add old files
      oldFiles.forEach((file, index) => {
        formData.append('old_files', file);
      });
      
      // Add new files
      newFiles.forEach((file, index) => {
        formData.append('new_files', file);
      });

      const uploadResponse = await apiFetch(`/advanced-processing/${sessionId}/upload-files`, {
        method: 'POST',
        body: formData
      });

      const uploadData = await uploadResponse.json();
      updateStep('upload', { status: 'completed', progress: 100 });
      addLog(`✅ تم رفع ${oldFiles.length + newFiles.length} ملف بنجاح`);
      
      // تحديث التقدم بعد رفع الملفات
      setState(prev => ({ ...prev, progress: 15 }));

      // Step 3: Start processing
      updateStep('processing', { status: 'processing', progress: 40 });
      addLog('⚙️ بدء معالجة الملفات...');

      // بدء التقدم الأولي فوراً
      setState(prev => ({ ...prev, progress: 20 })); // تعيين تقدم أولي

      // Poll for results
      await pollForResults(sessionId);

    } catch (error) {
      console.error('❌ خطأ في المعالجة المجمعة:', error);
      addLog(`❌ خطأ: ${error}`, 'error');
      stopVisualProgress(); // إيقاف التقدم المرئي عند الخطأ
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'حدث خطأ غير متوقع'
      }));
      toast.error('فشل في المعالجة المجمعة');
    }
  }, [apiFetch, addLog, updateStep, startVisualProgress, stopVisualProgress]);

  const pollForResults = useCallback(async (sessionId: string) => {
    const maxAttempts = 120; // 10 minutes max
    let attempts = 0;
    let lastProgressUpdate = Date.now();

    const poll = async () => {
      try {
        attempts++;
        
        const statusResponse = await apiFetch(`/advanced-processing/${sessionId}/status`);
        const statusData = await statusResponse.json();
        
        addLog(`📊 حالة المعالجة: ${statusData.status} (${statusData.progress?.toFixed(1) || 0}%)`);
        
        // Update overall progress and current file
        setState(prev => {
          const serverProgress = statusData.progress || 0;
          
          // إذا لم يكن هناك تقدم من الخادم، احسب التقدم بناءً على الخطوات المكتملة
          let calculatedProgress = serverProgress;
          if (statusData.processing_steps && (serverProgress === 0 || !statusData.progress)) {
            const completedSteps = statusData.processing_steps.filter((step: BatchProcessingStep) => step.status === 'completed').length;
            const processingSteps = statusData.processing_steps.filter((step: BatchProcessingStep) => step.status === 'processing').length;
            const totalSteps = statusData.processing_steps.length;
            
            // حساب التقدم: خطوات مكتملة + نصف نقطة للخطوات قيد المعالجة
            calculatedProgress = ((completedSteps + (processingSteps * 0.5)) / totalSteps) * 100;
            console.log(`📊 تقدم محسوب: ${calculatedProgress}% (مكتمل: ${completedSteps}, معالجة: ${processingSteps}, إجمالي: ${totalSteps})`);
          }
          
          // تأكد من التقدم المستمر - إضافة حد أدنى من التقدم مع الوقت
          const timeBasedProgress = Math.min(attempts * 2, 20); // حد أقصى 20% من الوقت فقط
          
          // إذا كانت المعالجة قيد التقدم، تأكد من زيادة التقدم بمرور الوقت
          const timeSinceLastUpdate = Date.now() - lastProgressUpdate;
          let progressBoost = 0;
          if (statusData.status === 'processing' && prev.progress < 90 && timeSinceLastUpdate > 10000) { // 10 ثوان
            progressBoost = Math.min(5, 90 - prev.progress); // زيادة 5% كحد أقصى
          }
          
          const finalProgress = Math.max(calculatedProgress, serverProgress, timeBasedProgress, prev.progress + progressBoost);
          
          // إذا تغير التقدم فعلاً، حدث وقت آخر تحديث
          if (finalProgress > prev.progress) {
            lastProgressUpdate = Date.now();
          }
          
          console.log(`🔄 تحديث التقدم: ${finalProgress}% (خادم: ${serverProgress}%, محسوب: ${calculatedProgress}%, زمني: ${timeBasedProgress}%, دفعة: ${progressBoost}%, سابق: ${prev.progress}%)`);
          
          return {
            ...prev,
            progress: Math.min(finalProgress, 99), // لا تصل 100% إلا عند الاكتمال الفعلي
            currentFile: statusData.current_step || prev.currentFile
          };
        });

        // Update processing steps based on server status
        if (statusData.processing_steps) {
          setState(prev => ({
            ...prev,
            processingSteps: statusData.processing_steps.map((serverStep: BatchProcessingStep) => ({
              id: serverStep.id,
              name: serverStep.name,
              status: serverStep.status,
              progress: serverStep.progress,
              duration: serverStep.duration,
              details: serverStep.details
            }))
          }));
          
          // إعادة حساب التقدم بعد تحديث الخطوات
          calculateProgress();
        }

        if (statusData.status === 'completed') {
          // Get final results
          const resultsResponse = await apiFetch(`/advanced-processing/${sessionId}/results`);
          const resultsData = await resultsResponse.json();
          
          // إيقاف التقدم المرئي
          stopVisualProgress();
          
          setState(prev => ({
            ...prev,
            isLoading: false,
            batchResult: {
              session_id: resultsData.session_id,
              total_files: resultsData.total_files || 0,
              processed_files: resultsData.total_files || 0,
              successful_comparisons: resultsData.successful_comparisons || 0,
              failed_comparisons: resultsData.failed_comparisons || 0,
              average_similarity: resultsData.average_similarity || 0,
              total_processing_time: resultsData.total_processing_time || 0,
              file_results: resultsData.file_results || [],
              summary_report: resultsData.summary?.toString() || 'تمت المعالجة بنجاح'
            },
            progress: 100
          }));
          
          updateStep('report', { status: 'completed', progress: 100 });
          addLog(`🎉 اكتملت المعالجة المجمعة: ${resultsData.successful_comparisons || 0}/${resultsData.total_files || 0} مقارنة ناجحة`);
          toast.success(`تمت المعالجة بنجاح: ${resultsData.successful_comparisons} مقارنة`);
          return;
        }
        
        if (statusData.status === 'failed' || statusData.status === 'error') {
          stopVisualProgress(); // إيقاف التقدم المرئي عند الخطأ
          throw new Error(statusData.error_message || 'فشلت المعالجة');
        }
        
        if (attempts >= maxAttempts) {
          throw new Error('انتهت مهلة المعالجة');
        }
        
        // Continue polling
        setTimeout(poll, 5000); // Poll every 5 seconds
        
      } catch (error) {
        console.error('❌ خطأ في استطلاع النتائج:', error);
        stopVisualProgress(); // إيقاف التقدم المرئي عند الخطأ
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error.message : 'حدث خطأ في المعالجة'
        }));
        toast.error('فشل في الحصول على النتائج');
      }
    };

    poll();
  }, [apiFetch, addLog, updateStep, calculateProgress, stopVisualProgress]);

  const resetBatchComparison = useCallback(() => {
    stopVisualProgress(); // إيقاف التقدم المرئي
    setState({
      isLoading: false,
      error: null,
      sessionId: null,
      batchResult: null,
      processingSteps: [...initialSteps],
      logs: [],
      progress: 0,
      currentFile: null
    });
  }, [stopVisualProgress]);

  const downloadBatchReport = useCallback(async () => {
    if (!state.sessionId) return;
    
    try {
      const response = await apiFetch(`/advanced-processing/${state.sessionId}/download-report`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch_comparison_report_${state.sessionId}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success('تم تحميل التقرير الشامل');
    } catch (error) {
      console.error('❌ خطأ في تحميل التقرير:', error);
      toast.error('فشل في تحميل التقرير');
    }
  }, [state.sessionId, apiFetch]);

  React.useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    };
  }, []);

  return {
    ...state,
    startBatchComparison,
    resetBatchComparison,
    downloadBatchReport,
    addLog
  };
}; 