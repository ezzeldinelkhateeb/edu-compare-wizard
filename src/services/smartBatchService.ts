/**
 * خدمة المعالجة الجماعية الذكية
 * Smart Batch Processing Service
 */

import { toast } from 'sonner';

export interface SmartBatchRequest {
  old_directory: string;
  new_directory: string;
  max_workers?: number;
  visual_threshold?: number;
  processing_mode?: 'gemini_only' | 'landingai_gemini';
}

export interface SmartBatchResponse {
  session_id: string;
  status: string;
  message: string;
}

export interface SmartBatchFileResult {
  old_file: string;
  new_file: string;
  stage_reached: number;
  visual_similarity?: number;
  has_text_content?: boolean;
  text_extraction?: {
    old_text: string;
    new_text: string;
    extraction_time: number;
  };
  ai_analysis?: {
    similarity_percentage: number;
    content_changes: string[];
    summary: string;
    processing_time: number;
  };
  overall_similarity: number;
  processing_time: number;
  cost_saved: number;
  status: string;
  error?: string;
}

export interface SmartBatchStats {
  total_pairs: number;
  stage_1_filtered: number;
  stage_2_processed: number;
  stage_3_analyzed: number;
  total_cost_saved: number;
  total_processing_time: number;
  average_similarity: number;
  efficiency_score: number;
  cost_savings_percentage: number;
}

export interface SmartBatchResult {
  session_id: string;
  status: string;
  results: SmartBatchFileResult[];
  stats: SmartBatchStats;
  message: string;
}

export interface SmartBatchSession {
  session_id: string;
  status: string;
  total_pairs: number;
  created_at: number;
}

class SmartBatchService {
  private static instance: SmartBatchService;
  private baseUrl: string;
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

  constructor() {
    this.baseUrl = '/api/v1/smart-batch';
  }

  static getInstance(): SmartBatchService {
    if (!SmartBatchService.instance) {
      SmartBatchService.instance = new SmartBatchService();
    }
    return SmartBatchService.instance;
  }

  /**
   * بدء المعالجة الجماعية الذكية
   * Start smart batch processing
   */
  async startBatchProcess(request: SmartBatchRequest): Promise<SmartBatchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/start-batch-process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_directory: request.old_directory,
          new_directory: request.new_directory,
          max_workers: request.max_workers || 4,
          visual_threshold: request.visual_threshold || 0.95,
          processing_mode: request.processing_mode || 'landingai_gemini'
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في بدء المعالجة: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      
      toast.success(`تم بدء المعالجة الذكية بنجاح! 🧠`, {
        description: `رقم الجلسة: ${result.session_id}`,
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      toast.error(`فشل في بدء المعالجة الذكية: ${errorMessage}`);
      throw error;
    }
  }

  /**
   * بدء المعالجة الجماعية الذكية بملفات مرفوعة
   * Start smart batch processing with uploaded files
   */
  async startBatchProcessWithFiles(
    oldFiles: File[],
    newFiles: File[],
    options: {
      max_workers?: number;
      visual_threshold?: number;
      processing_mode?: 'gemini_only' | 'landingai_gemini';
    } = {}
  ): Promise<SmartBatchResponse> {
    try {
      console.log('🚀 بدء المعالجة الذكية للملفات:', {
        oldFilesCount: oldFiles.length,
        newFilesCount: newFiles.length,
        options
      });

      // إنشاء FormData لرفع الملفات
      const formData = new FormData();
      
      // إضافة الملفات القديمة
      oldFiles.forEach((file, index) => {
        console.log(`📁 إضافة ملف قديم ${index + 1}: ${file.name} (${file.size} bytes)`);
        formData.append('old_files', file);
      });
      
      // إضافة الملفات الجديدة
      newFiles.forEach((file, index) => {
        console.log(`📁 إضافة ملف جديد ${index + 1}: ${file.name} (${file.size} bytes)`);
        formData.append('new_files', file);
      });
      
      // إضافة الإعدادات
      formData.append('max_workers', (options.max_workers || 4).toString());
      formData.append('visual_threshold', (options.visual_threshold || 0.95).toString());
      formData.append('processing_mode', options.processing_mode || 'landingai_gemini');

      console.log('📤 إرسال الطلب للباك إند...');
      const response = await fetch(`${this.baseUrl}/start-batch-process-files`, {
        method: 'POST',
        body: formData,
      });

      console.log('📥 استلام الرد من الباك إند:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ خطأ في الباك إند:', errorData);
        throw new Error(`فشل في بدء المعالجة: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ تم بدء المعالجة بنجاح:', result);
      
      toast.success(`تم بدء المعالجة الذكية للملفات! 🧠`, {
        description: `${oldFiles.length + newFiles.length} ملف - رقم الجلسة: ${result.session_id}`,
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      console.error('❌ فشل في بدء المعالجة الذكية:', error);
      toast.error(`فشل في بدء المعالجة الذكية: ${errorMessage}`);
      throw error;
    }
  }

  /**
   * فحص حالة المعالجة الجماعية
   * Check batch processing status
   */
  async getBatchStatus(sessionId: string): Promise<SmartBatchResult> {
    try {
      console.log(`🔍 فحص حالة الجلسة: ${sessionId}`);
      
      const response = await fetch(`${this.baseUrl}/batch-status/${sessionId}`);

      console.log('📥 استلام حالة الجلسة:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('❌ خطأ في فحص الحالة:', errorData);
        throw new Error(`فشل في فحص الحالة: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      console.log('✅ حالة الجلسة:', {
        sessionId: result.session_id,
        status: result.status,
        message: result.message,
        stats: result.stats,
        resultsCount: result.results?.length || 0
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      console.error('❌ خطأ في فحص الحالة:', error);
      throw new Error(`خطأ في فحص الحالة: ${errorMessage}`);
    }
  }

  /**
   * قائمة جلسات المعالجة
   * List batch processing sessions
   */
  async listBatchSessions(): Promise<{
    sessions: SmartBatchSession[];
    total_sessions: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/batch-sessions`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في جلب القائمة: ${errorData.detail || response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      throw new Error(`خطأ في جلب القائمة: ${errorMessage}`);
    }
  }

  /**
   * حذف جلسة معالجة
   * Delete batch processing session
   */
  async deleteBatchSession(sessionId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/batch-sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في حذف الجلسة: ${errorData.detail || response.statusText}`);
      }

      toast.success('تم حذف الجلسة بنجاح! 🗑️');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      toast.error(`فشل في حذف الجلسة: ${errorMessage}`);
      throw error;
    }
  }

  /**
   * الحصول على معلومات النظام
   * Get system information
   */
  async getSystemInfo(): Promise<{
    system_name: string;
    version: string;
    features: string[];
    pipeline_stages: Array<{
      stage: number;
      name: string;
      cost: string;
      description: string;
    }>;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/system-info`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في جلب معلومات النظام: ${errorData.detail || response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      throw new Error(`خطأ في جلب معلومات النظام: ${errorMessage}`);
    }
  }

  /**
   * بدء مراقبة الحالة تلقائياً
   * Start automatic status monitoring
   */
  startStatusPolling(
    sessionId: string,
    callback: (result: SmartBatchResult) => void,
    intervalMs: number = 3000
  ): void {
    // منع تكرار المراقبة لنفس الجلسة
    if (this.pollingIntervals.has(sessionId)) {
      console.log(`⚠️ مراقبة الحالة تعمل بالفعل للجلسة: ${sessionId}`);
      return;
    }

    console.log(`🚀 بدء مراقبة الحالة للجلسة: ${sessionId} (كل ${intervalMs}ms)`);
    
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 3;
    
    const pollStatus = async () => {
      try {
        const status = await this.getBatchStatus(sessionId);
        
        // إعادة تعيين عداد الأخطاء عند النجاح
        consecutiveErrors = 0;
        
        console.log('📊 تحديث حالة المعالجة:', {
          sessionId,
          status: status.status,
          message: status.message,
          stats: status.stats,
          resultsCount: status.results?.length || 0,
          timestamp: new Date().toISOString()
        });
        
        // طباعة تفاصيل الإحصائيات
        if (status.stats) {
          console.log('📈 تفاصيل الإحصائيات:', {
            total_pairs: status.stats.total_pairs,
            stage_1_filtered: status.stats.stage_1_filtered,
            stage_2_processed: status.stats.stage_2_processed,
            stage_3_analyzed: status.stats.stage_3_analyzed,
            total_processing_time: status.stats.total_processing_time
          });
        }
        
        // طباعة آخر النتائج
        if (status.results && status.results.length > 0) {
          const lastResult = status.results[status.results.length - 1];
          console.log('🔄 آخر نتيجة معالجة:', {
            filename: lastResult.old_file || lastResult.new_file,
            status: lastResult.status,
            stage_reached: lastResult.stage_reached,
            overall_similarity: lastResult.overall_similarity
          });
        }
        
        // مراقبة اللوجات الخاصة من الباك إند
        if (status.message && status.message.includes('FRONTEND_LOG:')) {
          console.log('🔍 لوج من الباك إند:', status.message);
          
          // تحليل اللوجات الخاصة
          if (status.message.includes('GEMINI_PROMPT_START')) {
            console.log('📝 بدء نص البرومبت المرسل لـ Gemini...');
          } else if (status.message.includes('GEMINI_PROMPT_END')) {
            console.log('📝 انتهاء نص البرومبت المرسل لـ Gemini');
          } else if (status.message.includes('GEMINI_RESPONSE_START')) {
            console.log('🤖 بدء رد Gemini...');
          } else if (status.message.includes('GEMINI_RESPONSE_END')) {
            console.log('🤖 انتهاء رد Gemini');
          } else if (status.message.includes('LANDINGAI_OLD_EXTRACTION_START')) {
            console.log('📄 بدء استخراج النص من الصورة القديمة...');
          } else if (status.message.includes('LANDINGAI_OLD_EXTRACTION_END')) {
            console.log('📄 انتهاء استخراج النص من الصورة القديمة');
          } else if (status.message.includes('LANDINGAI_NEW_EXTRACTION_START')) {
            console.log('📄 بدء استخراج النص من الصورة الجديدة...');
          } else if (status.message.includes('LANDINGAI_NEW_EXTRACTION_END')) {
            console.log('📄 انتهاء استخراج النص من الصورة الجديدة');
          } else if (status.message.includes('LANDINGAI_EXTRACTION_SUCCESS')) {
            console.log('✅ نجح استخراج النص من LandingAI');
          } else if (status.message.includes('LANDINGAI_EXTRACTION_FAILED')) {
            console.log('❌ فشل استخراج النص من LandingAI');
          } else if (status.message.includes('GEMINI_ERROR_START')) {
            console.log('❌ خطأ في Gemini AI');
          } else if (status.message.includes('GEMINI_ERROR_END')) {
            console.log('❌ انتهاء خطأ Gemini AI');
          } else if (status.message.includes('GEMINI_PROMPT_CREATED_START')) {
            console.log('📝 تم إنشاء البرومبت لـ Gemini...');
          } else if (status.message.includes('GEMINI_PROMPT_CREATED_END')) {
            console.log('📝 انتهاء إنشاء البرومبت لـ Gemini');
          } else if (status.message.includes('GEMINI_RESPONSE_RAW_START')) {
            console.log('🤖 بدء الرد الخام من Gemini...');
          } else if (status.message.includes('GEMINI_RESPONSE_RAW_END')) {
            console.log('🤖 انتهاء الرد الخام من Gemini');
          }
        }
        
        // عرض النصوص المستخرجة والردود بشكل أوضح
        if (status.message && status.message.includes('FRONTEND_LOG:') && status.message.includes('GEMINI_PROMPT_START')) {
          const promptText = status.message.replace('🔍 FRONTEND_LOG: GEMINI_PROMPT_START', '').replace('🔍 FRONTEND_LOG: GEMINI_PROMPT_END', '');
          console.log('📝 البرومبت المرسل لـ Gemini:', promptText);
        }
        
        if (status.message && status.message.includes('FRONTEND_LOG:') && status.message.includes('GEMINI_RESPONSE_START')) {
          const responseText = status.message.replace('🔍 FRONTEND_LOG: GEMINI_RESPONSE_START', '').replace('🔍 FRONTEND_LOG: GEMINI_RESPONSE_END', '');
          console.log('🤖 رد Gemini:', responseText);
        }
        
        if (status.message && status.message.includes('FRONTEND_LOG:') && status.message.includes('LANDINGAI_OLD_EXTRACTION_START')) {
          const oldText = status.message.replace('🔍 FRONTEND_LOG: LANDINGAI_OLD_EXTRACTION_START', '').replace('🔍 FRONTEND_LOG: LANDINGAI_OLD_EXTRACTION_END', '');
          console.log('📄 النص المستخرج من الصورة القديمة:', oldText);
        }
        
        if (status.message && status.message.includes('FRONTEND_LOG:') && status.message.includes('LANDINGAI_NEW_EXTRACTION_START')) {
          const newText = status.message.replace('🔍 FRONTEND_LOG: LANDINGAI_NEW_EXTRACTION_START', '').replace('🔍 FRONTEND_LOG: LANDINGAI_NEW_EXTRACTION_END', '');
          console.log('📄 النص المستخرج من الصورة الجديدة:', newText);
        }
        
        callback(status);
        
        // إيقاف المراقبة إذا اكتملت المعالجة أو فشلت
        if (status.status === 'مكتمل' || status.status === 'فشل') {
          console.log('✅ اكتملت المعالجة أو فشلت، إيقاف المراقبة');
          this.stopStatusPolling(sessionId);
        }
      } catch (error) {
        consecutiveErrors++;
        console.error(`❌ خطأ في مراقبة الحالة (${consecutiveErrors}/${maxConsecutiveErrors}):`, error);
        
        // إيقاف المراقبة في حالة أخطاء متكررة
        if (consecutiveErrors >= maxConsecutiveErrors) {
          console.log('🛑 عدد كبير من الأخطاء المتتالية، إيقاف المراقبة');
          this.stopStatusPolling(sessionId);
          return;
        }
        
        // إيقاف المراقبة في حالة خطأ متكرر
        if (error instanceof Error && error.message.includes('Failed to fetch')) {
          console.log('🔄 محاولة إعادة الاتصال...');
          // لا نوقف المراقبة فوراً، نعطي فرصة للاتصال
        }
      }
    };

    // بدء المراقبة
    const interval = setInterval(pollStatus, intervalMs);
    this.pollingIntervals.set(sessionId, interval);
    
    // تشغيل فوري
    pollStatus();
  }

  /**
   * إيقاف مراقبة الحالة
   * Stop status monitoring
   */
  stopStatusPolling(sessionId: string): void {
    const interval = this.pollingIntervals.get(sessionId);
    if (interval) {
      clearInterval(interval);
      this.pollingIntervals.delete(sessionId);
      console.log(`🛑 تم إيقاف مراقبة الحالة للجلسة: ${sessionId}`);
    }
  }

  /**
   * إيقاف جميع عمليات المراقبة
   * Stop all status monitoring
   */
  stopAllPolling(): void {
    this.pollingIntervals.forEach((interval) => {
      clearInterval(interval);
    });
    this.pollingIntervals.clear();
  }

  /**
   * تنسيق وقت المعالجة
   * Format processing time
   */
  formatProcessingTime(seconds: number): string {
    if (seconds < 60) {
      return `${seconds.toFixed(1)} ثانية`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes} دقيقة ${remainingSeconds.toFixed(0)} ثانية`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours} ساعة ${minutes} دقيقة`;
    }
  }

  /**
   * حساب نسبة التوفير
   * Calculate savings percentage
   */
  calculateSavingsPercentage(stats: SmartBatchStats): number {
    /*
     * نموذج التكلفة:
     * - المرحلة 1 (تطابق بصري عالي): 0 استدعاء API ⇒ تكلفة 0
     * - المرحلة 2 (استخراج النص فقط ثم توقف): 1 استدعاء API ⇒ تكلفة 1
     * - المرحلة 3 (تحسين النص + تحليل Gemini): 2 استدعاء-ات API ⇒ تكلفة 2
     * - baseline (بدون النظام الذكي): 3 استدعاء-ات API لكل زوج (استخراج نص 2× + تحليل عميق)
     */

    const defaultCost = stats.total_pairs * 3; // تكلفة خط الأساس

    const actualCost =
      (stats.stage_1_filtered * 0) + // لا تكلفة
      (stats.stage_2_processed * 1) + // تكلفة 1 لكل زوج توقف في المرحلة 2
      (stats.stage_3_analyzed * 2);   // تكلفة 2 لكل زوج وصل للمرحلة 3 (تحليل كامل)

    const savings = ((defaultCost - actualCost) / defaultCost) * 100;
    return Math.max(0, Math.min(100, savings));
  }

  /**
   * تنظيف الموارد
   * Cleanup resources
   */
  cleanup(): void {
    this.stopAllPolling();
  }
}

export default SmartBatchService; 