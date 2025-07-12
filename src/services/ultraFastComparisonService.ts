/**
 * خدمة المقارنة السريعة مع المعالجة المتوازية
 * Ultra Fast Comparison Service with Parallel Processing
 */

import { toast } from 'sonner';

export interface UltraFastComparisonResult {
  session_id: string;
  old_image_path: string;
  new_image_path: string;
  old_text_extraction: {
    success: boolean;
    text: string;
    confidence: number;
    word_count: number;
    processing_time: number;
    service: string;
    error?: string;
  };
  new_text_extraction: {
    success: boolean;
    text: string;
    confidence: number;
    word_count: number;
    processing_time: number;
    service: string;
    error?: string;
  };
  visual_comparison: {
    success: boolean;
    similarity: number;
    ssim_score: number;
    processing_time: number;
    changed_regions: unknown[];
    error?: string;
  };
  gemini_analysis: {
    success: boolean;
    similarity_percentage: number;
    content_changes: string[];
    summary: string;
    processing_time: number;
    error?: string;
  };
  overall_similarity: number;
  total_processing_time: number;
  parallel_efficiency: number;
  success: boolean;
  completed_at: string;
  session_info: {
    session_id: string;
    old_image_name: string;
    new_image_name: string;
    created_at: string;
    completed_at: string;
    total_processing_time: number;
  };
}

export interface ComparisonStatus {
  session_id: string;
  task_id: string;
  state: string;
  status: string;
  message: string;
  progress: number;
  stage?: string;
  current_file?: string;
  result_available?: boolean;
  error?: string;
  old_image_name: string;
  new_image_name: string;
  created_at: string;
}

export interface SessionInfo {
  session_id: string;
  status: string;
  progress: number;
  old_image_name: string;
  new_image_name: string;
  created_at: string;
  task_id: string;
}

class UltraFastComparisonService {
  private static instance: UltraFastComparisonService;
  private baseUrl: string;
  private statusCallbacks: Map<string, (status: ComparisonStatus) => void> = new Map();
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

  constructor() {
    this.baseUrl = '/api/ultra-fast';
  }

  static getInstance(): UltraFastComparisonService {
    if (!UltraFastComparisonService.instance) {
      UltraFastComparisonService.instance = new UltraFastComparisonService();
    }
    return UltraFastComparisonService.instance;
  }

  /**
   * بدء مقارنة سريعة لصورتين
   * Start ultra-fast comparison of two images
   */
  async startComparison(oldImage: File, newImage: File): Promise<{
    session_id: string;
    task_id: string;
    status: string;
    estimated_time: string;
    endpoints: {
      status: string;
      result: string;
      cancel: string;
    };
  }> {
    try {
      const formData = new FormData();
      formData.append('old_image', oldImage);
      formData.append('new_image', newImage);

      const response = await fetch(`${this.baseUrl}/upload-and-compare`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في بدء المقارنة: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      
      toast.success(`تم بدء المقارنة السريعة بنجاح! 🚀`, {
        description: `الوقت المتوقع: ${result.estimated_time}`,
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      toast.error(`فشل في بدء المقارنة: ${errorMessage}`);
      throw error;
    }
  }

  /**
   * فحص حالة المقارنة
   * Check comparison status
   */
  async getStatus(sessionId: string): Promise<ComparisonStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/status/${sessionId}`);

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
   * الحصول على نتيجة المقارنة
   * Get comparison result
   */
  async getResult(sessionId: string): Promise<UltraFastComparisonResult> {
    try {
      const response = await fetch(`${this.baseUrl}/result/${sessionId}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في الحصول على النتيجة: ${errorData.detail || response.statusText}`);
      }

      const result = await response.json();
      
      toast.success(`تم الحصول على نتيجة المقارنة! ✅`, {
        description: `معدل التشابه: ${(result.overall_similarity * 100).toFixed(1)}%`,
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      toast.error(`فشل في الحصول على النتيجة: ${errorMessage}`);
      throw error;
    }
  }

  /**
   * إلغاء المقارنة
   * Cancel comparison
   */
  async cancelComparison(sessionId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/cancel/${sessionId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في إلغاء المقارنة: ${errorData.detail || response.statusText}`);
      }

      // إيقاف التحديث التلقائي
      this.stopStatusPolling(sessionId);
      
      toast.info(`تم إلغاء المقارنة بنجاح 🚫`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      toast.error(`فشل في إلغاء المقارنة: ${errorMessage}`);
      throw error;
    }
  }

  /**
   * تنظيف ملفات الجلسة
   * Cleanup session files
   */
  async cleanupSession(sessionId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/cleanup/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في تنظيف الجلسة: ${errorData.detail || response.statusText}`);
      }

      toast.success(`تم تنظيف الجلسة بنجاح 🗑️`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      toast.error(`فشل في تنظيف الجلسة: ${errorMessage}`);
      throw error;
    }
  }

  /**
   * عرض جميع الجلسات النشطة
   * List all active sessions
   */
  async listActiveSessions(): Promise<{
    total_sessions: number;
    sessions: SessionInfo[];
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`فشل في عرض الجلسات: ${errorData.detail || response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      throw new Error(`خطأ في عرض الجلسات: ${errorMessage}`);
    }
  }

  /**
   * بدء التحديث التلقائي لحالة المقارنة
   * Start automatic status polling
   */
  startStatusPolling(
    sessionId: string,
    callback: (status: ComparisonStatus) => void,
    intervalMs: number = 2000
  ): void {
    // إيقاف أي تحديث سابق
    this.stopStatusPolling(sessionId);

    // حفظ الـ callback
    this.statusCallbacks.set(sessionId, callback);

    // بدء التحديث الدوري
    const interval = setInterval(async () => {
      try {
        const status = await this.getStatus(sessionId);
        callback(status);

        // إيقاف التحديث عند اكتمال المقارنة أو فشلها
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
          this.stopStatusPolling(sessionId);
        }
      } catch (error) {
        console.error(`خطأ في تحديث حالة الجلسة ${sessionId}:`, error);
        // في حالة الخطأ، نحاول مرة أخرى
      }
    }, intervalMs);

    this.pollingIntervals.set(sessionId, interval);
  }

  /**
   * إيقاف التحديث التلقائي لحالة المقارنة
   * Stop automatic status polling
   */
  stopStatusPolling(sessionId: string): void {
    const interval = this.pollingIntervals.get(sessionId);
    if (interval) {
      clearInterval(interval);
      this.pollingIntervals.delete(sessionId);
    }
    this.statusCallbacks.delete(sessionId);
  }

  /**
   * مقارنة كاملة مع انتظار النتيجة
   * Complete comparison with result waiting
   */
  async performFullComparison(
    oldImage: File,
    newImage: File,
    onProgress?: (status: ComparisonStatus) => void
  ): Promise<UltraFastComparisonResult> {
    // بدء المقارنة
    const startResult = await this.startComparison(oldImage, newImage);
    const sessionId = startResult.session_id;

    return new Promise((resolve, reject) => {
      // بدء التحديث التلقائي
      this.startStatusPolling(sessionId, async (status) => {
        // استدعاء callback التقدم إذا كان موجوداً
        if (onProgress) {
          onProgress(status);
        }

        // في حالة اكتمال المقارنة
        if (status.status === 'completed') {
          try {
            const result = await this.getResult(sessionId);
            resolve(result);
          } catch (error) {
            reject(error);
          }
        }
        // في حالة فشل المقارنة
        else if (status.status === 'failed') {
          reject(new Error(`فشلت المقارنة: ${status.error || 'خطأ غير معروف'}`));
        }
        // في حالة إلغاء المقارنة
        else if (status.status === 'cancelled') {
          reject(new Error('تم إلغاء المقارنة'));
        }
      });

      // timeout بعد 10 دقائق
      setTimeout(() => {
        this.stopStatusPolling(sessionId);
        reject(new Error('انتهت مهلة المقارنة (10 دقائق)'));
      }, 10 * 60 * 1000);
    });
  }

  /**
   * تنسيق وقت المعالجة
   * Format processing time
   */
  formatProcessingTime(seconds: number): string {
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)} ميلي ثانية`;
    } else if (seconds < 60) {
      return `${seconds.toFixed(1)} ثانية`;
    } else {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes} دقيقة و ${remainingSeconds.toFixed(1)} ثانية`;
    }
  }

  /**
   * حساب نسبة التحسن في السرعة
   * Calculate speed improvement percentage
   */
  calculateSpeedImprovement(parallelTime: number, sequentialTime: number): number {
    if (sequentialTime === 0) return 0;
    return ((sequentialTime - parallelTime) / sequentialTime) * 100;
  }

  /**
   * تنظيف جميع الـ polling النشطة
   * Clean up all active polling
   */
  cleanup(): void {
    // إيقاف جميع الـ intervals
    for (const [sessionId] of this.pollingIntervals) {
      this.stopStatusPolling(sessionId);
    }
  }
}

export default UltraFastComparisonService; 