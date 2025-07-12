import { useState, useCallback } from 'react';
import { toast } from 'sonner';

interface ProcessingStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  duration?: number;
  details?: string;
}

interface OCRResult {
  success: boolean;
  text: string;
  confidence: number;
  language: string;
  character_count: number;
  word_count: number;
  processing_time: number;
  image_info: {
    width: number;
    height: number;
    format: string;
    size_bytes: number;
  };
  extraction_details?: {
    total_chunks: number;
    chunks_by_type: Record<string, number>;
    text_elements: number;
    table_elements: number;
    image_elements: number;
  };
}

interface ComparisonResult {
  similarity_percentage: number;
  content_changes: string[];
  questions_changes: string[];
  major_differences: string[];
  added_content: string[];
  removed_content: string[];
  summary: string;
  recommendation: string;
  detailed_analysis: string;
  processing_time: number;
  confidence_score: number;
  old_text_length: number;
  new_text_length: number;
  common_words_count: number;
  unique_old_words: number;
  unique_new_words: number;
  service_used?: string;
}

interface VisualComparisonResult {
  similarity_score: number;
  ssim_score: number;
  phash_score: number;
  clip_score?: number;
  histogram_correlation: number;
  feature_matching_score: number;
  edge_similarity: number;
  layout_similarity: number;
  text_region_overlap: number;
  weights_used: Record<string, number>;
  processing_time: number;
  old_image_size: [number, number];
  new_image_size: [number, number];
  difference_detected: boolean;
  major_changes_detected: boolean;
  changed_regions: Array<{
    id: string;
    x: number;
    y: number;
    width: number;
    height: number;
    area: number;
    center: { x: number; y: number };
  }>;
  mean_squared_error: number;
  peak_signal_noise_ratio: number;
  content_type_detected: string;
  probable_content_match: boolean;
  analysis_summary: string;
  recommendations: string;
  confidence_notes: string;
  difference_map_path?: string;
}

interface LandingAIVerification {
  landing_ai_enabled: boolean;
  api_key_configured: boolean;
  agentic_doc_available: boolean;
  health_status: Record<string, unknown>;
  ocr_fallback_available: boolean;
  mock_mode: boolean;
  service_priority: string;
  configuration: {
    batch_size: number;
    max_workers: number;
    max_retries: number;
    include_marginalia: boolean;
    include_metadata: boolean;
    save_visual_groundings: boolean;
  };
  session_ocr_details?: {
    old_image_service: string;
    new_image_service: string;
    old_confidence: number;
    new_confidence: number;
    old_processing_time: number;
    new_processing_time: number;
  };
}

interface ComparisonState {
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  oldImageResult: OCRResult | null;
  newImageResult: OCRResult | null;
  comparisonResult: ComparisonResult | null;
  visualComparisonResult: VisualComparisonResult | null;
  landingAIVerification: LandingAIVerification | null;
  processingSteps: ProcessingStep[];
  logs: string[];
  progress: number;
}

const initialSteps: ProcessingStep[] = [
  { id: 'upload', name: 'رفع الملفات', status: 'pending', progress: 0 },
  { id: 'session', name: 'إنشاء جلسة المقارنة', status: 'pending', progress: 0 },
  { id: 'ocr_old', name: 'استخراج النص من الصورة القديمة', status: 'pending', progress: 0 },
  { id: 'ocr_new', name: 'استخراج النص من الصورة الجديدة', status: 'pending', progress: 0 },
  { id: 'ai_analysis', name: 'التحليل بالذكاء الاصطناعي', status: 'pending', progress: 0 },
  { id: 'report', name: 'إنشاء التقرير النهائي', status: 'pending', progress: 0 }
];

// مسار الـ API الأساسى (يجب أن يتماشى مع main.py -> settings.API_V1_STR)
const API_PREFIX = '/api/v1';

/**
 * يحاول الاتصال بالواجهة الخلفية.
 * يعطي الأولوية لمتغير البيئة VITE_BACKEND_URL، ثم يعود إلى استخدام المسارات النسبية (التي سيعترضها وكيل Vite).
 */
async function fetchWithFallback(path: string, options?: RequestInit): Promise<Response> {
  // استخدام الـ proxy بدلاً من الاتصال المباشر
  const url = path;
  
  // إضافة timeout طويل للطلبات التي قد تستغرق وقتاً طويلاً
  const timeoutMs = 300000; // 5 minutes
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
        // قراءة الجسم كـ JSON لمحاولة الحصول على تفاصيل الخطأ من الواجهة الخلفية
        const errorBody = await response.json().catch(() => ({ message: 'Could not parse error body' }));
        console.error(`⚠️ HTTP error! status: ${response.status}`, errorBody);
        // رمي خطأ يحتوي على معلومات مفيدة أكثر
        throw new Error(`Request to ${url} failed with status ${response.status}: ${errorBody.detail || response.statusText}`);
    }
    return response;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === 'AbortError') {
      console.error(`⏰ انتهت مهلة الطلب بعد ${timeoutMs / 1000} ثانية`);
      throw new Error(`انتهت مهلة الطلب - العملية استغرقت أكثر من ${timeoutMs / 1000} ثانية`);
    }
    console.error(`⚠️ فشل الاتصال بـ ${url}:`, err);
    // إعادة رمي الخطأ للتعامل معه في الكود الذي استدعى الدالة
    throw err;
  }
}

export const useRealComparison = () => {
  const [state, setState] = useState<ComparisonState>({
    isLoading: false,
    error: null,
    sessionId: null,
    oldImageResult: null,
    newImageResult: null,
    comparisonResult: null,
    visualComparisonResult: null,
    landingAIVerification: null,
    processingSteps: [...initialSteps],
    logs: [],
    progress: 0
  });

  const apiFetch = useCallback(
    async (path: string, options?: RequestInit) => {
      // إزالة /api/v1 من بداية المسار إذا كان موجوداً ثم إضافة API_PREFIX
      const cleanPath = path.startsWith('/api/v1') ? path.substring(7) : path;
      const correctedPath = cleanPath.startsWith('/') ? `${API_PREFIX}${cleanPath}` : `${API_PREFIX}/${cleanPath}`;
      return fetchWithFallback(correctedPath, options);
    },
    []
  );

  const addLog = useCallback((message: string, level: 'info' | 'error' | 'success' = 'info') => {
    const timestamp = new Date().toLocaleTimeString('ar-SA');
    const logEntry = `[${timestamp}] ${message}`;
    
    console.log(`🔍 ${logEntry}`);
    
    setState(prev => ({
      ...prev,
      logs: [...prev.logs.slice(-50), logEntry] // الاحتفاظ بآخر 50 سجل
    }));
  }, []);

  const updateStep = useCallback((stepId: string, updates: Partial<ProcessingStep>) => {
    setState(prev => ({
      ...prev,
      processingSteps: prev.processingSteps.map(step =>
        step.id === stepId ? { ...step, ...updates } : step
      )
    }));
  }, []);

  const updateProgress = useCallback(() => {
    setState(prev => {
      const completedSteps = prev.processingSteps.filter(step => step.status === 'completed').length;
      const totalSteps = prev.processingSteps.length;
      const progress = Math.round((completedSteps / totalSteps) * 100);
      
      return {
        ...prev,
        progress
      };
    });
  }, []);

  const startRealComparison = useCallback(async (oldImage: File, newImage: File) => {
    setState(prevState => ({
      ...prevState,
      isLoading: true,
      error: null,
      sessionId: null,
      oldImageResult: null,
      newImageResult: null,
      comparisonResult: null,
      visualComparisonResult: null,
      landingAIVerification: null,
      processingSteps: [...initialSteps],
      logs: []
    }));

    try {
      addLog('🚀 بدء عملية المقارنة الحقيقية باستخدام Landing AI و Gemini');
      addLog('📡 سيتم استخدام الخدمات الحقيقية وليس البيانات التجريبية');
      
      addLog('📤 بدء رفع الملفات...');
      const formData = new FormData();
      formData.append('old_image', oldImage);
      formData.append('new_image', newImage);
      addLog(`📁 ملفات المرفوعة: {oldImage: ${oldImage.name}, newImage: ${newImage.name}}`);
      
      updateStep('upload', { status: 'completed', progress: 100 });
      updateProgress();

      addLog('🔄 إنشاء جلسة مقارنة جديدة...');
      const sessionResponse = await apiFetch('/compare/create-session', {
        method: 'POST',
        body: formData,
      });

      if (!sessionResponse.ok) {
        throw new Error('فشل في إنشاء جلسة مقارنة');
      }
      
      const sessionData = await sessionResponse.json();
      const newSessionId = sessionData.session_id;

      setState(prev => ({...prev, sessionId: newSessionId}));
      addLog(`✅ تم إنشاء الجلسة بنجاح: ${newSessionId}`);
      updateStep('session', { status: 'completed', progress: 100 });
      updateProgress();

      // ... The rest of the comparison logic
      addLog('🔄 بدء المقارنة الكاملة (قد تستغرق عدة دقائق)...');
      updateStep('ocr', { status: 'processing', progress: 50 });
      updateProgress();
      
      const fullComparisonResponse = await apiFetch(`/compare/full-comparison/${newSessionId}`, {
          method: 'POST',
          body: formData,
      });

      if (!fullComparisonResponse.ok) {
          throw new Error('فشل في إجراء المقارنة الكاملة');
      }

      addLog('✅ تم الحصول على النتائج، جاري التحليل...');
      const results = await fullComparisonResponse.json();

      setState(prev => ({
        ...prev,
        isLoading: false,
        oldImageResult: results.old_image_result,
        newImageResult: results.new_image_result,
        comparisonResult: results.comparison_result,
        visualComparisonResult: results.visual_comparison_result,
        landingAIVerification: results.landing_ai_verification,
        processingSteps: prev.processingSteps.map(s => ({...s, status: 'completed', progress: 100}))
      }));

      toast.success('🎉 تمت عملية المقارنة بنجاح!');
      addLog('🎉 تمت عملية المقارنة بنجاح!');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'حدث خطأ غير معروف';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage
      }));
      toast.error(`❌ خطأ في المقارنة: ${errorMessage}`);
      addLog(`❌ خطأ: ${errorMessage}`, 'error');
    }
  }, [addLog, updateStep, updateProgress, apiFetch]);

  const resetComparison = useCallback(() => {
    console.log('🔄 إعادة تعيين المقارنة');
    setState({
      isLoading: false,
      error: null,
      sessionId: null,
      oldImageResult: null,
      newImageResult: null,
      comparisonResult: null,
      visualComparisonResult: null,
      landingAIVerification: null,
      processingSteps: [...initialSteps],
      logs: [],
      progress: 0
    });
  }, []);

  const downloadReport = useCallback(async () => {
    if (!state.sessionId) {
      toast.error('لا يوجد تقرير للتحميل');
      return;
    }

    try {
      addLog('📥 بدء تحميل التقرير...');
      
      const response = await fetchWithFallback(`${API_PREFIX}/compare/download-report/${state.sessionId}`);
      
      if (!response.ok) {
        throw new Error('فشل في تحميل التقرير');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `comparison-report-${state.sessionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      addLog('✅ تم تحميل التقرير بنجاح');
      toast.success('تم تحميل التقرير بنجاح');

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'فشل في تحميل التقرير';
      addLog(`❌ خطأ في التحميل: ${errorMessage}`, 'error');
      toast.error(errorMessage);
    }
  }, [state.sessionId, addLog]);

  const performVisualComparison = useCallback(async () => {
    if (!state.sessionId) {
      throw new Error('لا يوجد معرف جلسة');
    }

    addLog('🖼️ بدء المقارنة البصرية المحسنة...');

    try {
      const response = await fetchWithFallback(`${API_PREFIX}/compare/visual-analysis/${state.sessionId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في المقارنة البصرية: ${errorData.detail || response.statusText}`);
      }

      const visualResult: VisualComparisonResult = await response.json();

      setState(prev => ({
        ...prev,
        visualComparisonResult: visualResult
      }));

      addLog(`✅ اكتملت المقارنة البصرية: ${visualResult.similarity_score.toFixed(1)}% تطابق`);
      addLog(`🎯 ${visualResult.analysis_summary}`);

      return visualResult;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      addLog(`❌ فشل في المقارنة البصرية: ${errorMessage}`, 'error');
      throw error;
    }
  }, [state.sessionId, addLog]);

  const verifyLandingAI = useCallback(async () => {
    if (!state.sessionId) {
      throw new Error('لا يوجد معرف جلسة');
    }

    addLog('🔍 التحقق من استخدام Landing AI...');

    try {
      const response = await fetchWithFallback(`${API_PREFIX}/compare/verify-landingai/${state.sessionId}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في التحقق من Landing AI: ${errorData.detail || response.statusText}`);
      }

      const verification: LandingAIVerification = await response.json();

      setState(prev => ({
        ...prev,
        landingAIVerification: verification
      }));

      addLog(`📊 خدمة Landing AI: ${verification.landing_ai_enabled ? 'مُفعلة' : 'غير مُفعلة'}`);
      addLog(`🎯 الخدمة المستخدمة: ${verification.service_priority}`);
      
      if (verification.session_ocr_details) {
        addLog(`📝 خدمة الصورة القديمة: ${verification.session_ocr_details.old_image_service}`);
        addLog(`📝 خدمة الصورة الجديدة: ${verification.session_ocr_details.new_image_service}`);
      }

      return verification;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      addLog(`❌ فشل في التحقق من Landing AI: ${errorMessage}`, 'error');
      throw error;
    }
  }, [state.sessionId, addLog]);

  const forceLandingAI = useCallback(async () => {
    if (!state.sessionId) {
      throw new Error('لا يوجد معرف جلسة');
    }

    addLog('🚀 إجبار استخدام Landing AI...');

    try {
      const response = await fetchWithFallback(`${API_PREFIX}/compare/force-landing-ai/${state.sessionId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في إجبار Landing AI: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();

      setState(prev => ({
        ...prev,
        oldImageResult: result.old_image_result,
        newImageResult: result.new_image_result
      }));

      addLog(`✅ تم استخراج النص باستخدام Landing AI فقط`);
      addLog(`📊 الصورة القديمة: ${result.old_image_result.word_count} كلمة، ثقة: ${(result.old_image_result.confidence * 100).toFixed(1)}%`);
      addLog(`📊 الصورة الجديدة: ${result.new_image_result.word_count} كلمة، ثقة: ${(result.new_image_result.confidence * 100).toFixed(1)}%`);

      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      addLog(`❌ فشل في إجبار Landing AI: ${errorMessage}`, 'error');
      throw error;
    }
  }, [state.sessionId, addLog]);

  return {
    ...state,
    startRealComparison,
    performVisualComparison,
    verifyLandingAI,
    forceLandingAI,
    addLog,
    updateStep,
    updateProgress,
    resetComparison,
    downloadReport
  };
}; 