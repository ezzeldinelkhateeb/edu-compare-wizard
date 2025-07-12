/**
 * Hook للتكامل مع Backend FastAPI
 * Hook for FastAPI Backend Integration
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useToast } from '@/hooks/use-toast';
import { backendService, ProcessingProgress } from '@/services/backendServices';

export interface BackendComparisonState {
  // Session management
  currentSession: any | null;
  sessionError: string | null;
  
  // File upload
  isUploading: boolean;
  uploadProgress: Record<string, number>;
  uploadedFiles: {
    old: Array<{ file_id: string; filename: string; file_size: number }>;
    new: Array<{ file_id: string; filename: string; file_size: number }>;
  };
  
  // Comparison processing
  currentJob: any | null;
  isProcessing: boolean;
  processingProgress: ProcessingProgress | null;
  
  // Results
  comparisonResults: any | null;
  
  // WebSocket
  wsConnected: boolean;
  
  // Errors
  error: string | null;
}

export const useBackendComparison = () => {
  const { toast } = useToast();
  const wsRef = useRef<WebSocket | null>(null);

  const [state, setState] = useState<BackendComparisonState>({
    currentSession: null,
    sessionError: null,
    isUploading: false,
    uploadProgress: {},
    uploadedFiles: { old: [], new: [] },
    currentJob: null,
    isProcessing: false,
    processingProgress: null,
    comparisonResults: null,
    wsConnected: false,
    error: null
  });

  // تنظيف WebSocket عند unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      backendService.disconnectAllWebSockets();
    };
  }, []);

  /**
   * فحص صحة Backend
   */
  const checkBackendHealth = useCallback(async (): Promise<boolean> => {
    try {
      const health = await backendService.checkHealth();
      console.log('🏥 Backend Health:', health);
      
      if (health.status !== 'healthy') {
        setState(prev => ({ 
          ...prev, 
          error: 'Backend غير جاهز - تحقق من تشغيل الخدمات' 
        }));
        return false;
      }
      
      return true;
    } catch (error) {
      console.error('❌ Backend غير متاح:', error);
      setState(prev => ({ 
        ...prev, 
        error: 'لا يمكن الاتصال بـ Backend - تأكد من تشغيل الخادم على localhost:8001' 
      }));
      
      toast({
        title: "خطأ في الاتصال",
        description: "لا يمكن الاتصال بخادم المعالجة. تأكد من تشغيل Backend.",
        variant: "destructive"
      });
      
      return false;
    }
  }, [toast]);

  /**
   * إنشاء جلسة جديدة
   */
  const createSession = useCallback(async (sessionName?: string): Promise<string | null> => {
    try {
      setState(prev => ({ ...prev, sessionError: null, error: null }));
      
      // فحص Backend أولاً
      const isHealthy = await checkBackendHealth();
      if (!isHealthy) return null;
      
      const session = await backendService.createUploadSession(
        sessionName || `جلسة_${new Date().toLocaleDateString('ar-SA')}`
      );
      
      setState(prev => ({ 
        ...prev, 
        currentSession: session,
        uploadedFiles: { old: [], new: [] }
      }));
      
      toast({
        title: "تم إنشاء الجلسة",
        description: `جلسة جديدة: ${session.session_name}`,
      });
      
      console.log('✅ تم إنشاء جلسة:', session.session_id);
      return session.session_id;
      
    } catch (error) {
      console.error('❌ خطأ في إنشاء الجلسة:', error);
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      
      setState(prev => ({ 
        ...prev, 
        sessionError: errorMessage 
      }));
      
      toast({
        title: "خطأ في إنشاء الجلسة",
        description: errorMessage,
        variant: "destructive"
      });
      
      return null;
    }
  }, [checkBackendHealth, toast]);

  /**
   * رفع مجموعة ملفات
   */
  const uploadFiles = useCallback(async (
    files: File[], 
    fileType: 'old' | 'new',
    sessionId?: string
  ): Promise<boolean> => {
    try {
      const targetSessionId = sessionId || state.currentSession?.session_id;
      if (!targetSessionId) {
        throw new Error('لا توجد جلسة نشطة');
      }

      setState(prev => ({ 
        ...prev, 
        isUploading: true, 
        error: null 
      }));

      console.log(`📁 بدء رفع ${files.length} ملف ${fileType}`);

      // رفع الملفات بشكل متوازي (في مجموعات صغيرة)
      const batchSize = 3;
      const results = [];
      
      for (let i = 0; i < files.length; i += batchSize) {
        const batch = files.slice(i, i + batchSize);
        const batchPromises = batch.map(async (file) => {
          try {
            // تحديث التقدم
            setState(prev => ({
              ...prev,
              uploadProgress: {
                ...prev.uploadProgress,
                [file.name]: 50
              }
            }));

            const result = await backendService.uploadFile(file, targetSessionId, fileType);
            
            // تحديث التقدم
            setState(prev => ({
              ...prev,
              uploadProgress: {
                ...prev.uploadProgress,
                [file.name]: 100
              }
            }));

            return result;
          } catch (error) {
            console.error(`❌ فشل رفع ${file.name}:`, error);
            
            setState(prev => ({
              ...prev,
              uploadProgress: {
                ...prev.uploadProgress,
                [file.name]: -1 // خطأ
              }
            }));
            
            throw error;
          }
        });

        const batchResults = await Promise.allSettled(batchPromises);
        
        // معالجة النتائج
        batchResults.forEach((result, index) => {
          if (result.status === 'fulfilled') {
            results.push(result.value);
          } else {
            console.error(`❌ خطأ في رفع ${batch[index].name}:`, result.reason);
          }
        });
      }

      // تحديث قائمة الملفات المرفوعة
      setState(prev => ({
        ...prev,
        uploadedFiles: {
          ...prev.uploadedFiles,
          [fileType]: [
            ...prev.uploadedFiles[fileType],
            ...results.map(r => ({
              file_id: r.file_id,
              filename: r.filename,
              file_size: r.file_size
            }))
          ]
        },
        isUploading: false
      }));

      const successCount = results.length;
      const failCount = files.length - successCount;

      toast({
        title: "اكتمل الرفع",
        description: `تم رفع ${successCount} ملف${failCount > 0 ? ` (فشل ${failCount})` : ''}`,
        variant: failCount > 0 ? "destructive" : "default"
      });

      console.log(`✅ تم رفع ${successCount}/${files.length} ملف ${fileType}`);
      return successCount > 0;

    } catch (error) {
      console.error(`❌ خطأ في رفع الملفات:`, error);
      
      setState(prev => ({ 
        ...prev, 
        isUploading: false,
        error: error instanceof Error ? error.message : 'خطأ في رفع الملفات'
      }));

      toast({
        title: "خطأ في الرفع",
        description: error instanceof Error ? error.message : 'فشل في رفع الملفات',
        variant: "destructive"
      });

      return false;
    }
  }, [state.currentSession, toast]);

  /**
   * بدء عملية المقارنة
   */
  const startComparison = useCallback(async (sessionId?: string): Promise<string | null> => {
    try {
      const targetSessionId = sessionId || state.currentSession?.session_id;
      if (!targetSessionId) {
        throw new Error('لا توجد جلسة نشطة');
      }

      const oldFileIds = state.uploadedFiles.old.map(f => f.file_id);
      const newFileIds = state.uploadedFiles.new.map(f => f.file_id);

      if (oldFileIds.length === 0 || newFileIds.length === 0) {
        throw new Error('يجب رفع ملفات للمنهج القديم والجديد');
      }

      console.log('🚀 بدء المقارنة:', { oldFiles: oldFileIds.length, newFiles: newFileIds.length });

      const job = await backendService.startComparison(targetSessionId, oldFileIds, newFileIds);

      setState(prev => ({
        ...prev,
        currentJob: job,
        isProcessing: true,
        processingProgress: null,
        comparisonResults: null,
        error: null
      }));

      // بدء WebSocket للتقدم الحي
      connectWebSocket(job.job_id);

      toast({
        title: "بدأت المقارنة",
        description: "جاري معالجة الملفات...",
      });

      return job.job_id;

    } catch (error) {
      console.error('❌ خطأ في بدء المقارنة:', error);
      
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'خطأ في بدء المقارنة'
      }));

      toast({
        title: "خطأ في بدء المقارنة",
        description: error instanceof Error ? error.message : 'فشل في بدء المقارنة',
        variant: "destructive"
      });

      return null;
    }
  }, [state.currentSession, state.uploadedFiles, toast]);

  /**
   * الاتصال بـ WebSocket للتقدم الحي
   */
  const connectWebSocket = useCallback((jobId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = backendService.connectWebSocket(
      jobId,
      (data) => {
        console.log('📨 WebSocket message:', data);

        if (data.type === 'progress_update') {
          setState(prev => ({
            ...prev,
            processingProgress: {
              ...prev.processingProgress,
              ...data.data,
              job_id: jobId
            } as ProcessingProgress
          }));
        } 
        else if (data.type === 'stage_update') {
          setState(prev => ({
            ...prev,
            processingProgress: {
              ...prev.processingProgress,
              current_stage: data.data.stage,
              message: data.data.message
            } as ProcessingProgress
          }));
        }
        else if (data.type === 'job_completed') {
          setState(prev => ({
            ...prev,
            isProcessing: false,
            comparisonResults: data.data.result,
            processingProgress: {
              ...prev.processingProgress,
              progress_percentage: 100,
              status: 'completed'
            } as ProcessingProgress
          }));

          toast({
            title: "اكتملت المقارنة",
            description: "تم الانتهاء من معالجة جميع الملفات",
          });

          // قطع اتصال WebSocket
          if (wsRef.current) {
            wsRef.current.close();
          }
        }
        else if (data.type === 'error') {
          setState(prev => ({
            ...prev,
            isProcessing: false,
            error: data.data.error_message
          }));

          toast({
            title: "خطأ في المعالجة",
            description: data.data.error_message,
            variant: "destructive"
          });
        }
        else if (data.type === 'connection_established') {
          setState(prev => ({ ...prev, wsConnected: true }));
          console.log('🔌 تم الاتصال بـ WebSocket');
        }
      },
      (error) => {
        console.error('❌ خطأ WebSocket:', error);
        setState(prev => ({ ...prev, wsConnected: false }));
      }
    );

    wsRef.current = ws;

    ws.onopen = () => {
      setState(prev => ({ ...prev, wsConnected: true }));
    };

    ws.onclose = () => {
      setState(prev => ({ ...prev, wsConnected: false }));
    };

  }, [toast]);

  /**
   * إلغاء المقارنة
   */
  const cancelComparison = useCallback(async (): Promise<boolean> => {
    try {
      if (!state.currentJob) {
        throw new Error('لا توجد مقارنة نشطة للإلغاء');
      }

      await backendService.cancelComparison(state.currentJob.job_id);

      setState(prev => ({
        ...prev,
        isProcessing: false,
        currentJob: null,
        processingProgress: null
      }));

      // قطع اتصال WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }

      toast({
        title: "تم الإلغاء",
        description: "تم إلغاء عملية المقارنة",
      });

      return true;

    } catch (error) {
      console.error('❌ خطأ في إلغاء المقارنة:', error);
      
      toast({
        title: "خطأ في الإلغاء",
        description: error instanceof Error ? error.message : 'فشل في إلغاء المقارنة',
        variant: "destructive"
      });

      return false;
    }
  }, [state.currentJob, toast]);

  /**
   * إعادة تعيين الحالة
   */
  const resetState = useCallback(() => {
    // قطع WebSocket
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    setState({
      currentSession: null,
      sessionError: null,
      isUploading: false,
      uploadProgress: {},
      uploadedFiles: { old: [], new: [] },
      currentJob: null,
      isProcessing: false,
      processingProgress: null,
      comparisonResults: null,
      wsConnected: false,
      error: null
    });
  }, []);

  return {
    // State
    ...state,
    
    // Actions
    checkBackendHealth,
    createSession,
    uploadFiles,
    startComparison,
    cancelComparison,
    resetState,
    
    // Computed
    canStartComparison: state.uploadedFiles.old.length > 0 && state.uploadedFiles.new.length > 0 && !state.isProcessing,
    totalFilesUploaded: state.uploadedFiles.old.length + state.uploadedFiles.new.length,
    progressPercentage: state.processingProgress?.progress_percentage || 0,
    currentStage: state.processingProgress?.current_stage || 'IDLE',
    currentFile: state.processingProgress?.current_file,
  };
}; 