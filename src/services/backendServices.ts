/**
 * خدمات التكامل مع Backend FastAPI
 * Backend FastAPI Integration Services
 */

import { supabase } from '@/integrations/supabase/client';

// Backend base URL – override by setting VITE_BACKEND_URL in your env
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL ?? '/api/v1';
// Derive WebSocket base URL from HTTP base URL
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export interface UploadSession {
  session_id: string;
  session_name: string;
  created_at: string;
  status: string;
  message: string;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_type: 'old' | 'new';
  file_size: number;
  upload_url: string;
  message: string;
}

export interface ComparisonJob {
  job_id: string;
  session_id: string;
  status: string;
  message: string;
}

export interface ProcessingProgress {
  job_id: string;
  session_id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  current_stage: string;
  progress_percentage: number;
  current_file?: string;
  files_processed: number;
  total_files: number;
  estimated_time_remaining?: number;
  message?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface ProcessingResult {
  id: string;
  fileName: string;
  extractedText: string;
  confidence: number;
  fileUrl: string;
  jsonData: unknown;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

export interface ComparisonResult {
  id: string;
  oldFileName: string;
  newFileName: string;
  similarity: number;
  analysis: {
    similarity_percentage: number;
    content_changes: string[];
    questions_changes: string[];
    examples_changes: string[];
    major_differences: string[];
    summary: string;
    recommendation: string;
  };
  detailedReport: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

export interface ComparisonFileResult {
  old_file: string;
  new_file: string;
  visual_comparison?: { [key: string]: unknown };
  text_comparison?: { [key:string]: unknown };
  overall_similarity?: number;
  error?: string;
  status: string;
}

export interface ComparisonSessionResult {
  session_id: string;
  job_id: string;
  session_name?: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  total_files: number;
  processed_files: number;
  identical_files: number;
  changed_files: number;
  failed_files: number;
  average_visual_similarity: number;
  average_text_similarity: number;
  average_overall_similarity: number;
  file_results: ComparisonFileResult[];
  total_processing_time?: number;
  created_at: string;
  completed_at?: string;
}

class BackendService {
  private static instance: BackendService;
  private wsConnections: Map<string, WebSocket> = new Map();
  // use the unified base URL (can be overridden via env)
  private baseUrl: string = API_BASE_URL;

  static getInstance(): BackendService {
    if (!BackendService.instance) {
      BackendService.instance = new BackendService();
    }
    return BackendService.instance;
  }

  /**
   * فحص صحة Backend
   */
  async checkHealth(): Promise<{ status: string; services: Record<string, string> }> {
    try {
      const response = await fetch(API_BASE_URL.replace('/api/v1', '') + '/health');
      return await response.json();
    } catch (error) {
      console.error('❌ فشل في الاتصال بـ Backend:', error);
      throw new Error('Backend غير متاح');
    }
  }

  /**
   * إنشاء جلسة رفع جديدة
   */
  async createUploadSession(sessionName: string, description?: string): Promise<string> {
    try {
      console.log(`🔄 محاولة الاتصال بـ ${this.baseUrl}/upload/session`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(`${this.baseUrl}/upload/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_name: sessionName,
          description: description || 'جلسة رفع جديدة'
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'فشل في قراءة رسالة الخطأ');
        console.error(`❌ خطأ HTTP ${response.status}:`, errorText);
        throw new Error(`فشل في إنشاء الجلسة: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ تم إنشاء جلسة رفع جديدة:', data.session_id);
      return data.session_id;
    } catch (error) {
      if (error.name === 'AbortError') {
        console.error('❌ انتهت مهلة الاتصال بالخادم الخلفي');
        throw new Error('انتهت مهلة الاتصال - تأكد من تشغيل الخادم الخلفي على http://localhost:8001');
      }
      console.error('❌ فشل في إنشاء جلسة الرفع:', error);
      throw error instanceof Error ? error : new Error('خطأ غير معروف في إنشاء الجلسة');
    }
  }

  /**
   * رفع ملف واحد
   */
  async uploadFile(
    file: File, 
    sessionId: string, 
    fileType: 'old' | 'new'
  ): Promise<ProcessingResult> {
    try {
      console.log(`بدء رفع ${fileType} ملف: ${file.name}`);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);
      formData.append('file_type', fileType);

      const response = await fetch(`${this.baseUrl}/upload/file`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`فشل في رفع الملف: ${response.status}`);
      }

      const data = await response.json();
      
      const result: ProcessingResult = {
        id: data.file_id,
        fileName: file.name,
        extractedText: '', // سيتم استخراجه لاحقاً
        confidence: 0,
        fileUrl: data.upload_url,
        jsonData: null,
        status: 'completed'
      };

      console.log('تم رفع الملف بنجاح:', result);
      return result;

    } catch (error) {
      console.error(`خطأ في رفع ${fileType} ملف ${file.name}:`, error);
      return {
        id: crypto.randomUUID(),
        fileName: file.name,
        extractedText: '',
        confidence: 0,
        fileUrl: '',
        jsonData: null,
        status: 'error'
      };
    }
  }

  /**
   * رفع مجموعة ملفات
   */
  async uploadBatchFiles(files: File[], sessionId: string, fileType: 'old' | 'new'): Promise<FileUploadResponse[]> {
    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));
      formData.append('session_id', sessionId);
      formData.append('file_type', fileType);

      const response = await fetch(`${API_BASE_URL}/upload/batch`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log(`✅ تم رفع ${data.length} ملف ${fileType}`);
      return data;
    } catch (error) {
      console.error(`❌ خطأ في رفع الملفات:`, error);
      throw error;
    }
  }

  /**
   * بدء عملية المقارنة
   */
  async startComparison(
    sessionId: string,
    oldFileIds: string[],
    newFileIds: string[]
  ): Promise<string> {
    try {
      console.log('بدء عملية المقارنة للجلسة:', sessionId);

      const response = await fetch(`${this.baseUrl}/compare/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          old_files: oldFileIds,
          new_files: newFileIds,
          comparison_settings: {}
        })
      });

      if (!response.ok) {
        throw new Error(`فشل في بدء المقارنة: ${response.status}`);
      }

      const data = await response.json();
      console.log('تم بدء المقارنة بنجاح:', data.job_id);
      return data.job_id;

    } catch (error) {
      console.error('فشل في بدء المقارنة:', error);
      throw error;
    }
  }

  /**
   * الحصول على حالة المقارنة
   */
  async getComparisonStatus(jobId: string): Promise<ProcessingProgress> {
    try {
      const response = await fetch(`${this.baseUrl}/compare/status/${jobId}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ خطأ في جلب الحالة ${response.status}:`, errorText);
        throw new Error(`فشل في جلب الحالة: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('فشل في جلب حالة المقارنة:', error);
      throw error;
    }
  }

  /**
   * الحصول على نتيجة المقارنة
   */
  async getComparisonResults(jobId: string): Promise<ComparisonSessionResult> {
    try {
      console.log(`جلب نتائج المقارنة للوظيفة: ${jobId}`);
      const response = await fetch(`${this.baseUrl}/compare/result/${jobId}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("خطأ من السيرفر:", errorText);
        throw new Error(`فشل في جلب النتائج: ${response.status}`);
      }

      const data = await response.json();
      console.log("تم جلب النتائج بنجاح:", data);
      return data;
    } catch (error) {
      console.error(' فشل في جلب نتائج المقارنة:', error);
      throw error;
    }
  }

  /**
   * إلغاء عملية المقارنة
   */
  async cancelComparison(jobId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/compare/job/${jobId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('🛑 تم إلغاء الوظيفة:', jobId);
      return data;
    } catch (error) {
      console.error(`❌ خطأ في إلغاء الوظيفة ${jobId}:`, error);
      throw error;
    }
  }

  /**
   * الاتصال بـ WebSocket للتقدم الحي
   */
  connectWebSocket(jobId: string, onMessage: (data: unknown) => void, onError?: (error: unknown) => void): WebSocket {
    const wsUrl = `${WS_BASE_URL}/ws/${jobId}`;
    
    // إغلاق الاتصال السابق إن وجد
    this.disconnectWebSocket(jobId);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`🔌 تم الاتصال بـ WebSocket للوظيفة: ${jobId}`);
      this.wsConnections.set(jobId, ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`📨 رسالة WebSocket:`, data);
        onMessage(data);
      } catch (error) {
        console.error('❌ خطأ في تحليل رسالة WebSocket:', error);
      }
    };

    ws.onclose = () => {
      console.log(`🔌 تم قطع اتصال WebSocket للوظيفة: ${jobId}`);
      this.wsConnections.delete(jobId);
    };

    ws.onerror = (error) => {
      console.error(`❌ خطأ WebSocket للوظيفة ${jobId}:`, error);
      if (onError) onError(error);
    };

    return ws;
  }

  /**
   * قطع اتصال WebSocket
   */
  disconnectWebSocket(jobId: string): void {
    const ws = this.wsConnections.get(jobId);
    if (ws) {
      ws.close();
      this.wsConnections.delete(jobId);
      console.log(`🔌 تم قطع اتصال WebSocket للوظيفة: ${jobId}`);
    }
  }

  /**
   * قطع جميع اتصالات WebSocket
   */
  disconnectAllWebSockets(): void {
    this.wsConnections.forEach((ws, jobId) => {
      ws.close();
      console.log(`🔌 تم قطع اتصال WebSocket للوظيفة: ${jobId}`);
    });
    this.wsConnections.clear();
  }

  /**
   * الحصول على معلومات الجلسة
   */
  async getSessionInfo(sessionId: string): Promise<unknown> {
    try {
      const response = await fetch(`${API_BASE_URL}/upload/session/${sessionId}`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`❌ خطأ في جلب معلومات الجلسة ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * حذف الجلسة
   */
  async deleteSession(sessionId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/upload/session/${sessionId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('🗑️ تم حذف الجلسة:', sessionId);
      return data;
    } catch (error) {
      console.error(`❌ خطأ في حذف الجلسة ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * الحصول على قائمة الجلسات
   */
  async listSessions(): Promise<{ sessions: unknown[]; total_sessions: number }> {
    try {
      const response = await fetch(`${API_BASE_URL}/upload/sessions`);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ خطأ في جلب قائمة الجلسات:', error);
      throw error;
    }
  }

  // رفع متعدد الملفات
  async uploadMultipleFiles(
    oldFiles: File[],
    newFiles: File[],
    sessionId: string,
    onProgress: (progress: number, currentFile: string, fileType: string) => void
  ): Promise<{ oldResults: ProcessingResult[], newResults: ProcessingResult[] }> {
    
    const oldResults: ProcessingResult[] = [];
    const newResults: ProcessingResult[] = [];
    
    const totalFiles = oldFiles.length + newFiles.length;
    let processedFiles = 0;

    console.log(`بدء رفع ${totalFiles} ملف`);

    // رفع الملفات القديمة
    for (const file of oldFiles) {
      const currentProgress = (processedFiles / totalFiles) * 50;
      onProgress(currentProgress, file.name, 'الكتاب القديم');
      
      const result = await this.uploadFile(file, sessionId, 'old');
      oldResults.push(result);
      processedFiles++;
    }

    // رفع الملفات الجديدة
    for (const file of newFiles) {
      const currentProgress = 50 + (processedFiles / totalFiles) * 50;
      onProgress(currentProgress, file.name, 'الكتاب الجديد');
      
      const result = await this.uploadFile(file, sessionId, 'new');
      newResults.push(result);
      processedFiles++;
    }

    console.log('انتهت رفع جميع الملفات');
    return { oldResults, newResults };
  }

  // اختبار الاتصال بالباك إند
  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(API_BASE_URL.replace('/api/v1', '') + '/health');
      return response.ok;
    } catch (error) {
      console.error('فشل في الاتصال بالباك إند:', error);
      return false;
    }
  }
}

// إنشاء instance واحد
export const backendService = BackendService.getInstance();

// تنظيف عند إغلاق الصفحة
window.addEventListener('beforeunload', () => {
  backendService.disconnectAllWebSockets();
}); 