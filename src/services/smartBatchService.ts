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
          visual_threshold: request.visual_threshold || 0.95
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
    } = {}
  ): Promise<SmartBatchResponse> {
    try {
      // إنشاء FormData لرفع الملفات
      const formData = new FormData();
      
      // إضافة الملفات القديمة
      oldFiles.forEach((file, index) => {
        formData.append('old_files', file);
      });
      
      // إضافة الملفات الجديدة
      newFiles.forEach((file, index) => {
        formData.append('new_files', file);
      });
      
      // إضافة الإعدادات
      formData.append('max_workers', (options.max_workers || 4).toString());
      formData.append('visual_threshold', (options.visual_threshold || 0.95).toString());

      const response = await fetch(`${this.baseUrl}/start-batch-process-files`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في بدء المعالجة: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      
      toast.success(`تم بدء المعالجة الذكية للملفات! 🧠`, {
        description: `${oldFiles.length + newFiles.length} ملف - رقم الجلسة: ${result.session_id}`,
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
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
      const response = await fetch(`${this.baseUrl}/batch-status/${sessionId}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في فحص الحالة: ${errorData.detail || response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
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
    const pollStatus = async () => {
      try {
        const status = await this.getBatchStatus(sessionId);
        
        // إضافة console.log لتتبع التحديثات
        console.log('📊 تحديث حالة المعالجة:', {
          sessionId,
          status: status.status,
          message: status.message,
          stats: status.stats,
          resultsCount: status.results?.length || 0
        });
        
        callback(status);
        
        // إيقاف المراقبة إذا اكتملت المعالجة أو فشلت
        if (status.status === 'مكتمل' || status.status === 'فشل') {
          console.log('✅ اكتملت المعالجة أو فشلت، إيقاف المراقبة');
          this.stopStatusPolling(sessionId);
        }
      } catch (error) {
        console.error('❌ خطأ في مراقبة الحالة:', error);
        // لا نوقف المراقبة في حالة خطأ مؤقت
      }
    };

    // بدء المراقبة
    const interval = setInterval(pollStatus, intervalMs);
    this.pollingIntervals.set(sessionId, interval);
    
    console.log(`🚀 بدء مراقبة الحالة للجلسة: ${sessionId} (كل ${intervalMs}ms)`);
    
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