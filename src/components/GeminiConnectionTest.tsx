import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Wifi, CheckCircle, XCircle, AlertCircle, Brain } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { buildApiUrl, API_CONFIG } from '@/config/api';

interface GeminiHealthResponse {
  status: 'healthy' | 'unhealthy';
  mode: 'mock' | 'production';
  message: string;
  api_key_configured: boolean;
  model?: string;
  model_version?: string;
  test_response_length?: number;
  features?: string[];
  error?: string;
}

interface ServerHealthResponse {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version: string;
  services?: Record<string, string>;
  error?: string;
}

const GeminiConnectionTest: React.FC = () => {
  const [isTesting, setIsTesting] = useState(false);
  const [isTestingServer, setIsTestingServer] = useState(false);
  const [testResult, setTestResult] = useState<GeminiHealthResponse | null>(null);
  const [serverTestResult, setServerTestResult] = useState<ServerHealthResponse | null>(null);
  const [lastTestTime, setLastTestTime] = useState<string | null>(null);
  const [lastServerTestTime, setLastServerTestTime] = useState<string | null>(null);
  const { toast } = useToast();

  const testGeminiConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.AI_SERVICES_HEALTH));
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      const geminiHealth = data.services?.gemini;
      
      if (geminiHealth) {
        setTestResult(geminiHealth);
        setLastTestTime(new Date().toLocaleString('ar-SA'));
        
        if (geminiHealth.status === 'healthy') {
          toast({
            title: "✅ اتصال Gemini ناجح",
            description: geminiHealth.message,
            duration: 5000
          });
        } else {
          toast({
            title: "❌ فشل في الاتصال بـ Gemini",
            description: geminiHealth.message || geminiHealth.error,
            duration: 5000
          });
        }
      } else {
        throw new Error('لم يتم العثور على معلومات Gemini في الاستجابة');
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      setTestResult({
        status: 'unhealthy',
        mode: 'mock',
        message: 'فشل في الاتصال بالخادم',
        api_key_configured: false,
        error: errorMessage
      });
      
      toast({
        title: "❌ خطأ في الاتصال",
        description: errorMessage,
        duration: 5000
      });
    } finally {
      setIsTesting(false);
    }
  };

  const testServerConnection = async () => {
    setIsTestingServer(true);
    setServerTestResult(null);
    
    try {
      const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.HEALTH));
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setServerTestResult(data);
      setLastServerTestTime(new Date().toLocaleString('ar-SA'));
      
      if (data.status === 'healthy') {
        toast({
          title: "✅ اتصال الخادم ناجح",
          description: "الخادم يعمل بشكل طبيعي",
          duration: 3000
        });
      } else {
        toast({
          title: "❌ مشكلة في الخادم",
          description: data.error || "الخادم غير متاح",
          duration: 5000
        });
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      setServerTestResult({
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        version: 'unknown',
        error: errorMessage
      });
      
      toast({
        title: "❌ فشل في الاتصال بالخادم",
        description: errorMessage,
        duration: 5000
      });
    } finally {
      setIsTestingServer(false);
    }
  };

  const getStatusIcon = () => {
    if (isTesting) return <Loader2 className="w-5 h-5 animate-spin" />;
    if (!testResult) return <Wifi className="w-5 h-5 text-gray-400" />;
    
    switch (testResult.status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusBadge = () => {
    if (!testResult) return null;
    
    const variant = testResult.status === 'healthy' ? 'default' : 'destructive';
    const text = testResult.status === 'healthy' ? 'متصل' : 'غير متصل';
    
    return <Badge variant={variant} className="mr-2">{text}</Badge>;
  };

  const getModeBadge = () => {
    if (!testResult) return null;
    
    const variant = testResult.mode === 'production' ? 'default' : 'secondary';
    const text = testResult.mode === 'production' ? 'الإنتاج' : 'المحاكاة';
    
    return <Badge variant={variant}>{text}</Badge>;
  };

  return (
    <Card className="w-full max-w-sm mx-auto">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Brain className="w-4 h-4 text-blue-600" />
          اختبار الاتصال
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* أزرار الاختبار */}
        <div className="grid grid-cols-2 gap-2">
          <Button 
            onClick={testServerConnection}
            disabled={isTestingServer}
            className="w-full"
            variant={serverTestResult?.status === 'healthy' ? 'default' : 'outline'}
            size="sm"
          >
            {isTestingServer ? (
              <>
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                خادم...
              </>
            ) : (
              <>
                <Wifi className="w-3 h-3 mr-1" />
                الخادم
              </>
            )}
          </Button>
          
          <Button 
            onClick={testGeminiConnection}
            disabled={isTesting}
            className="w-full"
            variant={testResult?.status === 'healthy' ? 'default' : 'outline'}
            size="sm"
          >
            {isTesting ? (
              <>
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                Gemini...
              </>
            ) : (
              <>
                <Brain className="w-3 h-3 mr-1" />
                Gemini AI
              </>
            )}
          </Button>
        </div>

        {/* نتائج الاختبار */}
        {(testResult || serverTestResult) && (
          <div className="space-y-3">
            {/* نتيجة اختبار الخادم */}
            {serverTestResult && (
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    {serverTestResult.status === 'healthy' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className="text-sm font-medium">الخادم</span>
                  </div>
                  <Badge variant={serverTestResult.status === 'healthy' ? 'default' : 'destructive'}>
                    {serverTestResult.status === 'healthy' ? 'متصل' : 'غير متصل'}
                  </Badge>
                </div>
                
                <div className="text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-600">الإصدار:</span>
                    <span>{serverTestResult.version}</span>
                  </div>
                  {lastServerTestTime && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">آخر اختبار:</span>
                      <span>{lastServerTestTime}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* نتيجة اختبار Gemini */}
            {testResult && (
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2 bg-purple-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    {getStatusIcon()}
                    <span className="text-sm font-medium">Gemini AI</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge()}
                    {getModeBadge()}
                  </div>
                </div>

                {/* الرسالة */}
                <Alert variant={testResult.status === 'healthy' ? 'default' : 'destructive'}>
                  <AlertDescription className="text-sm">
                    {testResult.message}
                  </AlertDescription>
                </Alert>

                {/* التفاصيل */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">API Key:</span>
                    <span className={testResult.api_key_configured ? 'text-green-600' : 'text-red-600'}>
                      {testResult.api_key_configured ? 'مُعد' : 'غير مُعد'}
                    </span>
                  </div>
                  
                  {testResult.model && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">النموذج:</span>
                      <span className="font-mono text-sm">{testResult.model}</span>
                    </div>
                  )}
                  
                  {testResult.model_version && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">الإصدار:</span>
                      <span className="text-green-600 font-medium">{testResult.model_version}</span>
                    </div>
                  )}
                  
                  {testResult.features && (
                    <div className="mt-2">
                      <span className="text-gray-600 text-xs">الميزات:</span>
                      <div className="mt-1 space-y-1">
                        {testResult.features.map((feature, index) => (
                          <div key={index} className="text-xs text-blue-600 flex items-center gap-1">
                            <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                            {feature}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {testResult.test_response_length !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">طول الاستجابة:</span>
                      <span>{testResult.test_response_length} حرف</span>
                    </div>
                  )}
                  
                  {lastTestTime && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">آخر اختبار:</span>
                      <span className="text-xs">{lastTestTime}</span>
                    </div>
                  )}
                </div>

                {/* رسالة الخطأ */}
                {testResult.error && (
                  <Alert variant="destructive">
                    <AlertCircle className="w-4 h-4" />
                    <AlertDescription className="text-sm">
                      {testResult.error}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </div>
        )}

        {/* معلومات إضافية */}
        <div className="text-xs text-gray-500 text-center pt-2 border-t">
          يتحقق هذا الاختبار من اتصال الخادم و Gemini AI API
        </div>
      </CardContent>
    </Card>
  );
};

export default GeminiConnectionTest; 