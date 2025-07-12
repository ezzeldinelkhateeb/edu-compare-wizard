// خدمة المعالجة المتوازية لتسريع عمليات المقارنة
import { toast } from 'sonner';

export interface ParallelProcessingResult {
  oldTextExtraction: {
    success: boolean;
    text: string;
    confidence: number;
    processing_time: number;
    service_used: string;
    error?: string;
  };
  newTextExtraction: {
    success: boolean;
    text: string;
    confidence: number;
    processing_time: number;
    service_used: string;
    error?: string;
  };
  visualComparison: {
    success: boolean;
    similarity_score: number;
    ssim_score: number;
    processing_time: number;
    changed_regions: any[];
    error?: string;
  };
  geminiAnalysis: {
    success: boolean;
    similarity_percentage: number;
    content_changes: string[];
    summary: string;
    processing_time: number;
    error?: string;
  };
  totalProcessingTime: number;
  parallelEfficiency: number;
}

export interface WorkerTask {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  startTime?: number;
  endTime?: number;
  result?: any;
  error?: string;
}

class ParallelProcessingService {
  private static instance: ParallelProcessingService;
  private workers: Map<string, WorkerTask> = new Map();
  private progressCallbacks: ((tasks: WorkerTask[]) => void)[] = [];

  static getInstance(): ParallelProcessingService {
    if (!ParallelProcessingService.instance) {
      ParallelProcessingService.instance = new ParallelProcessingService();
    }
    return ParallelProcessingService.instance;
  }

  // تسجيل callback لتتبع التقدم
  onProgress(callback: (tasks: WorkerTask[]) => void) {
    this.progressCallbacks.push(callback);
  }

  // إشعار بتحديث التقدم
  private notifyProgress() {
    const tasks = Array.from(this.workers.values());
    this.progressCallbacks.forEach(callback => callback(tasks));
  }

  // تحديث حالة worker
  private updateWorkerStatus(workerId: string, updates: Partial<WorkerTask>) {
    const worker = this.workers.get(workerId);
    if (worker) {
      Object.assign(worker, updates);
      this.workers.set(workerId, worker);
      this.notifyProgress();
    }
  }

  // Worker 1: استخراج النص من الصورة القديمة
  private async extractOldText(sessionId: string, oldImageFile: File): Promise<any> {
    const workerId = 'old-text-extraction';
    this.workers.set(workerId, {
      id: workerId,
      name: 'استخراج النص - الصورة القديمة',
      status: 'running',
      progress: 0,
      startTime: Date.now()
    });

    try {
      this.updateWorkerStatus(workerId, { progress: 20 });

      const formData = new FormData();
      formData.append('image', oldImageFile);
      formData.append('sessionId', sessionId);
      formData.append('imageType', 'old');

      this.updateWorkerStatus(workerId, { progress: 40 });

      const response = await fetch('/api/extract-text', {
        method: 'POST',
        body: formData
      });

      this.updateWorkerStatus(workerId, { progress: 80 });

      const result = await response.json();

      this.updateWorkerStatus(workerId, { 
        progress: 100,
        status: 'completed',
        endTime: Date.now(),
        result
      });

      return result;
    } catch (error) {
      this.updateWorkerStatus(workerId, {
        status: 'error',
        endTime: Date.now(),
        error: error instanceof Error ? error.message : 'خطأ غير معروف'
      });
      throw error;
    }
  }

  // Worker 2: استخراج النص من الصورة الجديدة
  private async extractNewText(sessionId: string, newImageFile: File): Promise<any> {
    const workerId = 'new-text-extraction';
    this.workers.set(workerId, {
      id: workerId,
      name: 'استخراج النص - الصورة الجديدة',
      status: 'running',
      progress: 0,
      startTime: Date.now()
    });

    try {
      this.updateWorkerStatus(workerId, { progress: 20 });

      const formData = new FormData();
      formData.append('image', newImageFile);
      formData.append('sessionId', sessionId);
      formData.append('imageType', 'new');

      this.updateWorkerStatus(workerId, { progress: 40 });

      const response = await fetch('/api/extract-text', {
        method: 'POST',
        body: formData
      });

      this.updateWorkerStatus(workerId, { progress: 80 });

      const result = await response.json();

      this.updateWorkerStatus(workerId, { 
        progress: 100,
        status: 'completed',
        endTime: Date.now(),
        result
      });

      return result;
    } catch (error) {
      this.updateWorkerStatus(workerId, {
        status: 'error',
        endTime: Date.now(),
        error: error instanceof Error ? error.message : 'خطأ غير معروف'
      });
      throw error;
    }
  }

  // Worker 3: المقارنة البصرية
  private async performVisualComparison(sessionId: string): Promise<any> {
    const workerId = 'visual-comparison';
    this.workers.set(workerId, {
      id: workerId,
      name: 'المقارنة البصرية',
      status: 'running',
      progress: 0,
      startTime: Date.now()
    });

    try {
      this.updateWorkerStatus(workerId, { progress: 30 });

      const response = await fetch('/api/visual-comparison', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ sessionId })
      });

      this.updateWorkerStatus(workerId, { progress: 70 });

      const result = await response.json();

      this.updateWorkerStatus(workerId, { 
        progress: 100,
        status: 'completed',
        endTime: Date.now(),
        result
      });

      return result;
    } catch (error) {
      this.updateWorkerStatus(workerId, {
        status: 'error',
        endTime: Date.now(),
        error: error instanceof Error ? error.message : 'خطأ غير معروف'
      });
      throw error;
    }
  }

  // Worker 4: تحليل Gemini للنصوص
  private async performGeminiAnalysis(sessionId: string): Promise<any> {
    const workerId = 'gemini-analysis';
    this.workers.set(workerId, {
      id: workerId,
      name: 'تحليل Gemini',
      status: 'pending',
      progress: 0
    });

    // انتظار اكتمال استخراج النصوص أولاً
    const oldTextWorker = this.workers.get('old-text-extraction');
    const newTextWorker = this.workers.get('new-text-extraction');

    while (oldTextWorker?.status !== 'completed' || newTextWorker?.status !== 'completed') {
      if (oldTextWorker?.status === 'error' || newTextWorker?.status === 'error') {
        throw new Error('فشل في استخراج النصوص المطلوبة للتحليل');
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    this.updateWorkerStatus(workerId, { 
      status: 'running',
      progress: 10,
      startTime: Date.now()
    });

    try {
      this.updateWorkerStatus(workerId, { progress: 30 });

      const response = await fetch('/api/compare-texts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ sessionId })
      });

      this.updateWorkerStatus(workerId, { progress: 80 });

      const result = await response.json();

      this.updateWorkerStatus(workerId, { 
        progress: 100,
        status: 'completed',
        endTime: Date.now(),
        result
      });

      return result;
    } catch (error) {
      this.updateWorkerStatus(workerId, {
        status: 'error',
        endTime: Date.now(),
        error: error instanceof Error ? error.message : 'خطأ غير معروف'
      });
      throw error;
    }
  }

  // الدالة الرئيسية للمعالجة المتوازية
  async processComparison(
    sessionId: string,
    oldImageFile: File,
    newImageFile: File
  ): Promise<ParallelProcessingResult> {
    const startTime = Date.now();
    
    // إعادة تعيين الـ workers
    this.workers.clear();

    console.log('🚀 بدء المعالجة المتوازية للمقارنة');
    console.log('📁 الملفات:', {
      oldFile: oldImageFile.name,
      newFile: newImageFile.name,
      sessionId
    });

    try {
      // تشغيل العمليات الثلاث الأولى بشكل متوازي
      const [oldTextResult, newTextResult, visualResult] = await Promise.allSettled([
        this.extractOldText(sessionId, oldImageFile),
        this.extractNewText(sessionId, newImageFile),
        this.performVisualComparison(sessionId)
      ]);

      // تشغيل تحليل Gemini بعد اكتمال استخراج النصوص
      const geminiResult = await this.performGeminiAnalysis(sessionId);

      const endTime = Date.now();
      const totalProcessingTime = (endTime - startTime) / 1000;

      // حساب كفاءة المعالجة المتوازية
      const sequentialTime = this.calculateSequentialTime();
      const parallelEfficiency = ((sequentialTime - totalProcessingTime) / sequentialTime) * 100;

      const result: ParallelProcessingResult = {
        oldTextExtraction: this.extractWorkerResult(oldTextResult, 'old-text-extraction'),
        newTextExtraction: this.extractWorkerResult(newTextResult, 'new-text-extraction'),
        visualComparison: this.extractWorkerResult(visualResult, 'visual-comparison'),
        geminiAnalysis: this.extractGeminiResult(geminiResult),
        totalProcessingTime,
        parallelEfficiency: Math.round(parallelEfficiency)
      };

      console.log('✅ اكتملت المعالجة المتوازية');
      console.log('⏱️ إجمالي الوقت:', totalProcessingTime, 'ثانية');
      console.log('🚀 كفاءة التوازي:', parallelEfficiency, '%');

      toast.success(`اكتملت المقارنة في ${totalProcessingTime.toFixed(1)} ثانية مع كفاءة ${parallelEfficiency}%`);

      return result;

    } catch (error) {
      console.error('❌ خطأ في المعالجة المتوازية:', error);
      toast.error('حدث خطأ في المعالجة المتوازية');
      throw error;
    }
  }

  // استخراج نتيجة worker
  private extractWorkerResult(result: PromiseSettledResult<any>, workerId: string): any {
    if (result.status === 'fulfilled') {
      return {
        success: true,
        ...result.value,
        processing_time: this.getWorkerProcessingTime(workerId)
      };
    } else {
      return {
        success: false,
        error: result.reason?.message || 'خطأ غير معروف',
        processing_time: this.getWorkerProcessingTime(workerId)
      };
    }
  }

  // استخراج نتيجة Gemini
  private extractGeminiResult(result: any): any {
    return {
      success: true,
      ...result,
      processing_time: this.getWorkerProcessingTime('gemini-analysis')
    };
  }

  // حساب وقت معالجة worker
  private getWorkerProcessingTime(workerId: string): number {
    const worker = this.workers.get(workerId);
    if (worker?.startTime && worker?.endTime) {
      return (worker.endTime - worker.startTime) / 1000;
    }
    return 0;
  }

  // حساب الوقت المتوقع للمعالجة المتسلسلة
  private calculateSequentialTime(): number {
    // تقدير أوقات العمليات (بالثواني)
    const estimatedTimes = {
      textExtraction: 8, // 4 ثواني لكل صورة
      visualComparison: 6,
      geminiAnalysis: 5
    };
    
    return estimatedTimes.textExtraction + estimatedTimes.visualComparison + estimatedTimes.geminiAnalysis;
  }

  // الحصول على حالة جميع الـ workers
  getWorkersStatus(): WorkerTask[] {
    return Array.from(this.workers.values());
  }

  // إعادة تعيين الخدمة
  reset() {
    this.workers.clear();
    this.progressCallbacks = [];
  }
}

export const parallelProcessingService = ParallelProcessingService.getInstance();
