// تكوين API
export const API_CONFIG = {
  // عنوان الخادم - يمكن تغييره حسب البيئة
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  
  // نقاط النهاية
  ENDPOINTS: {
    HEALTH: '/api/v1/health',
    AI_SERVICES_HEALTH: '/api/v1/health/ai-services',
    COMPARE: '/api/v1/compare',
    UPLOAD: '/api/v1/upload',
    WEBSOCKET: '/api/v1/ws',
    ADVANCED_PROCESSING: '/api/v1/advanced-processing',
    SMART_BATCH: '/api/v1/smart-batch',
    MULTILINGUAL: '/api/v1/multilingual'
  },
  
  // إعدادات الطلبات
  REQUEST_CONFIG: {
    timeout: 30000, // 30 ثانية
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  }
};

// دالة مساعدة لبناء URL كامل
export const buildApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// دالة مساعدة للطلبات
export const apiRequest = async (
  endpoint: string, 
  options: RequestInit = {}
): Promise<Response> => {
  const url = buildApiUrl(endpoint);
  
  const config: RequestInit = {
    ...API_CONFIG.REQUEST_CONFIG,
    ...options,
    headers: {
      ...API_CONFIG.REQUEST_CONFIG.headers,
      ...options.headers
    }
  };
  
  return fetch(url, config);
}; 