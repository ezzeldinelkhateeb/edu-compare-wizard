import React, { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useRealComparison } from '@/hooks/useRealComparison';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  ArrowLeft,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

interface ComparisonDashboardProps {
  files: {
    old: File[];
    new: File[];
  };
  onBack: () => void;
}

export function ComparisonDashboard({ files, onBack }: ComparisonDashboardProps) {
  const { 
    isLoading, 
    error, 
    progress,
    sessionId,
    oldImageResult,
    newImageResult,
    comparisonResult,
    visualComparisonResult,
    landingAIVerification,
    processingSteps,
    logs,
    startRealComparison,
    performVisualComparison,
    verifyLandingAI,
    forceLandingAI,
    resetComparison,
    downloadReport
  } = useRealComparison();

  const formatNumber = (value: number | undefined | null, decimals = 2) => {
    return typeof value === 'number' && !isNaN(value) ? value.toFixed(decimals) : 'N/A';
  };

  useEffect(() => {
    console.log('🚀 ComparisonDashboard: بدء تشغيل لوحة المقارنة');
    console.log('📁 الملفات المرفوعة:', { 
      oldFiles: files.old.length, 
      newFiles: files.new.length 
    });

    if (files.old.length === 1 && files.new.length === 1) {
      console.log('🔄 بدء عملية المقارنة التلقائية');
      startRealComparison(files.old[0], files.new[0]);
    } else if (files.old.length > 1 || files.new.length > 1) {
      toast.error("يدعم النظام حالياً مقارنة ملف واحد فقط من كل نوع");
    }
  }, [files, startRealComparison]);

  const handleRetry = () => {
    if (files.old.length === 1 && files.new.length === 1) {
      resetComparison();
      setTimeout(() => {
        startRealComparison(files.old[0], files.new[0]);
      }, 500);
    }
  };

  // دالة للتحقق من Landing AI والمقارنة البصرية
  const handleAdvancedAnalysis = async () => {
    if (!sessionId) return;

    try {
      // التحقق من Landing AI
      const verification = await verifyLandingAI();
      console.log('🔍 تحقق Landing AI:', verification);

      // المقارنة البصرية
      const visualComparison = await performVisualComparison();
      console.log('🖼️ المقارنة البصرية:', visualComparison);

      console.log('✅ تم إجراء التحليل المتقدم بنجاح');
    } catch (error) {
      console.error('خطأ في التحليل المتقدم:', error);
    }
  };

  // دالة لإجبار استخدام Landing AI
  const handleForceLandingAI = async () => {
    if (!sessionId) return;

    try {
      const result = await forceLandingAI();
      console.log('🚀 نتيجة إجبار Landing AI:', result);
      console.log('✅ تم استخراج النص باستخدام Landing AI فقط');
    } catch (error) {
      console.error('خطأ في إجبار Landing AI:', error);
    }
  };

  if (isLoading) {
    console.log(`⏳ معالجة: ${progress}%`);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header with back button */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              {onBack && (
                <Button variant="outline" onClick={onBack} disabled={isLoading}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة
                </Button>
              )}
              <h1 className="text-3xl font-bold text-gray-900">معالجة المقارنة</h1>
            </div>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">جاري معالجة الملفات...</h2>
            <p className="text-lg text-gray-600">
              يتم الآن تحليل ومقارنة الملفات باستخدام خوارزميات الذكاء الاصطناعي
            </p>
          </div>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>التقدم الإجمالي</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-3" />
            </div>

            {/* عرض الخطوات */}
            <div className="space-y-3">
              {processingSteps.map((step, index) => (
                <div key={step.id} className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                    step.status === 'completed' ? 'bg-green-500' :
                    step.status === 'processing' ? 'bg-blue-500' :
                    step.status === 'error' ? 'bg-red-500' : 'bg-gray-300'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <span className="font-medium">{step.name}</span>
                    {step.status === 'processing' && (
                      <div className="text-sm text-blue-600">جاري المعالجة...</div>
                    )}
                    {step.duration && (
                      <div className="text-sm text-gray-500">({step.duration.toFixed(2)}s)</div>
                    )}
                    {step.details && (
                      <div className="text-sm text-gray-600">{step.details}</div>
                    )}
                  </div>
                  <Badge variant={step.status === 'completed' ? 'default' : 'secondary'}>
                    {step.status === 'completed' ? 'مكتمل' :
                     step.status === 'processing' ? 'جاري...' :
                     step.status === 'error' ? 'خطأ' : 'انتظار'}
                  </Badge>
                </div>
              ))}
            </div>

            {/* عرض آخر السجلات */}
            {logs.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">سجل العمليات</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1 font-mono text-sm max-h-32 overflow-y-auto">
                    {logs.slice(-5).map((log, index) => (
                      <div key={index} className="text-gray-700">{log}</div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    console.log('❌ خطأ في المقارنة:', error);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header with back button */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              {onBack && (
                <Button variant="outline" onClick={onBack}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة
                </Button>
              )}
              <h1 className="text-3xl font-bold text-gray-900">نتائج المقارنة</h1>
            </div>
          </div>

          <div className="text-center">
            <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-red-500" />
            <h2 className="text-2xl font-bold mb-2 text-red-600">حدث خطأ في المقارنة</h2>
            <p className="text-lg text-gray-600 mb-6">{error}</p>
            
            <Alert className="mb-6 text-right">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>تعليمات لحل المشكلة:</AlertTitle>
              <AlertDescription>
                <ul className="text-sm space-y-1 mt-2">
                  <li>• تأكد من تشغيل الخادم الخلفي على http://localhost:8000</li>
                  <li>• تأكد من تشغيل Redis Server</li>
                  <li>• تأكد من تشغيل Celery Worker</li>
                  <li>• راجع ملف TROUBLESHOOTING.md للمساعدة التفصيلية</li>
                </ul>
              </AlertDescription>
            </Alert>
            
            <div className="flex gap-4 justify-center">
              <Button onClick={handleRetry} disabled={isLoading}>
                <RefreshCw className="w-4 h-4 mr-2" />
                المحاولة مرة أخرى
              </Button>
              {onBack && (
                <Button variant="outline" onClick={onBack}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة للرفع
                </Button>
              )}
            </div>
          </div>
        </div>
      </section>
    );
  }

  // إذا لا يوجد ملفات مناسبة للمقارنة
  if (files.old.length === 0 || files.new.length === 0) {
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold mb-2">لا توجد ملفات للمقارنة</h2>
          <p className="text-lg text-gray-600 mb-6">
            يرجى رفع ملف واحد على الأقل في كل من المجلدين (القديم والجديد)
          </p>
          {onBack && (
            <Button onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              العودة للرفع
            </Button>
          )}
        </div>
      </section>
    );
  }

  // إذا كان يتم المعالجة أو لا توجد نتائج بعد، عرض شاشة المعالجة البسيطة
  if (isLoading || (!oldImageResult && !newImageResult && !comparisonResult && !error)) {
    console.log(`⏳ معالجة: ${progress}%`);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header with back button */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              {onBack && (
                <Button variant="outline" onClick={onBack} disabled={isLoading}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  العودة
                </Button>
              )}
              <h1 className="text-3xl font-bold text-gray-900">معالجة المقارنة</h1>
            </div>
          </div>

          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">جاري معالجة الملفات...</h2>
            <p className="text-lg text-gray-600">
              يتم الآن تحليل ومقارنة الملفات باستخدام خوارزميات الذكاء الاصطناعي
            </p>
          </div>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>التقدم الإجمالي</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-3" />
            </div>

            {/* عرض الخطوات */}
            <div className="space-y-3">
              {processingSteps.map((step, index) => (
                <div key={step.id} className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                    step.status === 'completed' ? 'bg-green-500' :
                    step.status === 'processing' ? 'bg-blue-500' :
                    step.status === 'error' ? 'bg-red-500' : 'bg-gray-300'
                  }`}>
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <span className="font-medium">{step.name}</span>
                    {step.status === 'processing' && (
                      <div className="text-sm text-blue-600">جاري المعالجة...</div>
                    )}
                    {step.duration && (
                      <div className="text-sm text-gray-500">({step.duration.toFixed(2)}s)</div>
                    )}
                  </div>
                  <Badge variant={step.status === 'completed' ? 'default' : 'secondary'}>
                    {step.status === 'completed' ? 'مكتمل' :
                     step.status === 'processing' ? 'جاري...' :
                     step.status === 'error' ? 'خطأ' : 'انتظار'}
                  </Badge>
                </div>
              ))}
            </div>

            {/* عرض آخر السجلات */}
            {logs.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">سجل العمليات</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-1 font-mono text-sm max-h-32 overflow-y-auto">
                    {logs.slice(-5).map((log, index) => (
                      <div key={index} className="text-gray-700">{log}</div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </section>
    );
  }

  // عرض التقرير المتقدم عند اكتمال المعالجة
  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6 bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">
          مقارنة المحتوى التعليمي المحسن
        </h1>
        <p className="text-gray-600">
          مقارنة ذكية باستخدام Landing AI + تحليل بصري محسن + Gemini AI
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 justify-center">
        <Button
          onClick={handleAdvancedAnalysis}
          disabled={!comparisonResult || isLoading}
          className="bg-purple-600 hover:bg-purple-700"
        >
          🔍 تحليل متقدم (بصري + تحقق Landing AI)
        </Button>
        
        <Button
          onClick={handleForceLandingAI}
          disabled={!sessionId || isLoading}
          variant="outline"
          className="border-orange-500 text-orange-600 hover:bg-orange-50"
        >
          🚀 إجبار استخدام Landing AI
        </Button>
      </div>

      {/* Landing AI Verification Display */}
      {landingAIVerification && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              🔍 نتائج التحقق من Landing AI
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>حالة Landing AI:</span>
                  <span className={landingAIVerification.landing_ai_enabled ? 'text-green-600 font-bold' : 'text-red-600'}>
                    {landingAIVerification.landing_ai_enabled ? '✅ مُفعل' : '❌ غير مُفعل'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>API Key:</span>
                  <span className={landingAIVerification.api_key_configured ? 'text-green-600' : 'text-red-600'}>
                    {landingAIVerification.api_key_configured ? '✅ مُعد' : '❌ غير مُعد'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>الخدمة المستخدمة:</span>
                  <span className="font-semibold">{landingAIVerification.service_priority}</span>
                </div>
                <div className="flex justify-between">
                  <span>وضع المحاكاة:</span>
                  <span className={landingAIVerification.mock_mode ? 'text-orange-600' : 'text-green-600'}>
                    {landingAIVerification.mock_mode ? '⚠️ مُفعل' : '✅ غير مُفعل'}
                  </span>
                </div>
              </div>
              
              {landingAIVerification.session_ocr_details && (
                <div className="space-y-2">
                  <h4 className="font-semibold">تفاصيل الجلسة الحالية:</h4>
                  <div className="text-sm space-y-1">
                    <div>خدمة الصورة القديمة: <span className="font-mono">{landingAIVerification.session_ocr_details.old_image_service}</span></div>
                    <div>خدمة الصورة الجديدة: <span className="font-mono">{landingAIVerification.session_ocr_details.new_image_service}</span></div>
                    <div>ثقة الصورة القديمة: <span className="font-bold">{formatNumber(landingAIVerification.session_ocr_details.old_confidence * 100, 1)}%</span></div>
                    <div>ثقة الصورة الجديدة: <span className="font-bold">{formatNumber(landingAIVerification.session_ocr_details.new_confidence * 100, 1)}%</span></div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Text Extraction Results - Primary Focus */}
      {(oldImageResult || newImageResult) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📄 نتائج استخراج النص باستخدام Landing AI
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Old Image Text */}
              {oldImageResult && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <h3 className="text-lg font-semibold text-gray-800">النص المستخرج - الصورة القديمة</h3>
                  </div>
                  
                  <div className="bg-blue-50 p-4 rounded-lg space-y-2">
                    <div className="text-sm text-gray-600 grid grid-cols-2 gap-2">
                      <span>عدد الكلمات: <strong>{oldImageResult.word_count || 'غير محدد'}</strong></span>
                      <span>عدد الأحرف: <strong>{oldImageResult.character_count || 'غير محدد'}</strong></span>
                      <span>مستوى الثقة: <strong className="text-green-600">{formatNumber((oldImageResult.confidence || 0) * 100, 1)}%</strong></span>
                      <span>وقت المعالجة: <strong>{formatNumber(oldImageResult.processing_time, 2)}s</strong></span>
                    </div>
                    
                    {oldImageResult.extraction_details && (
                      <div className="text-sm text-blue-700 bg-blue-100 p-2 rounded">
                        📊 تفاصيل الاستخراج: {oldImageResult.extraction_details.total_chunks} قطعة، 
                        {oldImageResult.extraction_details.text_elements} عنصر نصي، 
                        {oldImageResult.extraction_details.table_elements} جدول، 
                        {oldImageResult.extraction_details.image_elements} صورة
                      </div>
                    )}
                  </div>
                  
                  <div className="border rounded-lg p-4 bg-white">
                    <h4 className="font-semibold mb-2">النص المستخرج:</h4>
                    <div className="max-h-60 overflow-y-auto text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded">
                      {oldImageResult.text || 'لم يتم استخراج نص'}
                    </div>
                  </div>
                </div>
              )}

              {/* New Image Text */}
              {newImageResult && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <h3 className="text-lg font-semibold text-gray-800">النص المستخرج - الصورة الجديدة</h3>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg space-y-2">
                    <div className="text-sm text-gray-600 grid grid-cols-2 gap-2">
                      <span>عدد الكلمات: <strong>{newImageResult.word_count || 'غير محدد'}</strong></span>
                      <span>عدد الأحرف: <strong>{newImageResult.character_count || 'غير محدد'}</strong></span>
                      <span>مستوى الثقة: <strong className="text-green-600">{formatNumber((newImageResult.confidence || 0) * 100, 1)}%</strong></span>
                      <span>وقت المعالجة: <strong>{formatNumber(newImageResult.processing_time, 2)}s</strong></span>
                    </div>
                    
                    {newImageResult.extraction_details && (
                      <div className="text-sm text-green-700 bg-green-100 p-2 rounded">
                        📊 تفاصيل الاستخراج: {newImageResult.extraction_details.total_chunks} قطعة، 
                        {newImageResult.extraction_details.text_elements} عنصر نصي، 
                        {newImageResult.extraction_details.table_elements} جدول، 
                        {newImageResult.extraction_details.image_elements} صورة
                      </div>
                    )}
                  </div>
                  
                  <div className="border rounded-lg p-4 bg-white">
                    <h4 className="font-semibold mb-2">النص المستخرج:</h4>
                    <div className="max-h-60 overflow-y-auto text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded">
                      {newImageResult.text || 'لم يتم استخراج نص'}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* الهدف الرئيسي: مقارنة النصوص باستخدام Landing AI + Gemini */}
      {comparisonResult && (
        <Card className="border-2 border-purple-200 shadow-lg bg-gradient-to-br from-purple-25 to-blue-25">
          <CardHeader className="bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-t-lg">
            <CardTitle className="flex items-center gap-3 text-xl">
              🎯 **النتيجة الرئيسية**: تحليل المقارنة النصية الذكي
              <Badge className="bg-white text-purple-600 font-bold">
                Landing AI → Gemini
              </Badge>
              {comparisonResult.service_used && (
                <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                  {comparisonResult.service_used}
                </Badge>
              )}
            </CardTitle>
            <p className="text-purple-100 text-sm mt-1">
              🔍 استخراج النص من الصور → تحليل الاختلافات → معرفة الإضافات الجديدة بالمنهج
            </p>
          </CardHeader>
          <CardContent className="pt-6">
            {/* Overall Similarity Score - Enhanced */}
            <div className="text-center p-8 bg-gradient-to-r from-purple-50 via-blue-50 to-indigo-50 rounded-xl mb-8 border border-purple-200">
              <div className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600 mb-3">
                {formatNumber(comparisonResult.similarity_percentage, 1)}%
              </div>
              <div className="text-xl font-semibold text-gray-800 mb-3">نسبة التشابه النصي</div>
              <div className={`px-6 py-3 rounded-full text-base inline-block font-bold shadow-md ${
                comparisonResult.similarity_percentage >= 80 
                  ? 'bg-green-100 text-green-800 border border-green-300' 
                  : comparisonResult.similarity_percentage >= 60
                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                  : 'bg-red-100 text-red-800 border border-red-300'
              }`}>
                {comparisonResult.similarity_percentage >= 80 
                  ? '✅ محتوى متشابه جداً - تغييرات طفيفة' 
                  : comparisonResult.similarity_percentage >= 60
                  ? '⚠️ محتوى متشابه جزئياً - تحديثات متوسطة'
                  : '🔍 اختلافات كبيرة - تحديثات شاملة'}
              </div>
              
              {/* إضافة تفسير للنتيجة */}
              <div className="mt-4 p-4 bg-white rounded-lg border border-purple-100">
                <h4 className="font-semibold text-purple-800 mb-2">💡 تفسير النتيجة:</h4>
                <p className="text-sm text-gray-700">
                  {comparisonResult.similarity_percentage >= 80 
                    ? "المنهج محدث بتعديلات بسيطة. معظم المحتوى مُحافظ عليه مع إضافات أو تحسينات محدودة." 
                    : comparisonResult.similarity_percentage >= 60
                    ? "هناك تحديثات ملحوظة في المنهج. يُنصح بمراجعة التغييرات للتأكد من شمولية التدريس."
                    : "تم إجراء تحديثات شاملة على المنهج. مراجعة دقيقة مطلوبة لفهم كافة التغييرات."}
                </p>
              </div>
            </div>

            {/* Enhanced Statistics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
              <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-200 shadow-sm">
                <div className="text-2xl font-bold text-blue-600">{comparisonResult.old_text_length || 0}</div>
                <div className="text-sm text-gray-600">أحرف النص القديم</div>
                <div className="text-xs text-blue-500 mt-1">📄 المنهج الأصلي</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-xl border border-green-200 shadow-sm">
                <div className="text-2xl font-bold text-green-600">{comparisonResult.new_text_length || 0}</div>
                <div className="text-sm text-gray-600">أحرف النص الجديد</div>
                <div className="text-xs text-green-500 mt-1">📄 المنهج المحدث</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-xl border border-purple-200 shadow-sm">
                <div className="text-2xl font-bold text-purple-600">{comparisonResult.common_words_count || 0}</div>
                <div className="text-sm text-gray-600">كلمات مشتركة</div>
                <div className="text-xs text-purple-500 mt-1">🔗 محتوى محافظ عليه</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-xl border border-orange-200 shadow-sm">
                <div className="text-2xl font-bold text-orange-600">{formatNumber((comparisonResult.confidence_score || 0) * 100, 1)}%</div>
                <div className="text-sm text-gray-600">ثقة التحليل</div>
                <div className="text-xs text-orange-500 mt-1">🎯 دقة Gemini AI</div>
              </div>
            </div>

            {/* الهدف الأساسي: معرفة التحديثات والإضافات */}
            <div className="mb-8 p-6 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border-2 border-indigo-200">
              <h3 className="text-xl font-bold text-indigo-800 mb-4 flex items-center gap-2">
                🎯 الهدف من المقارنة: معرفة التحديثات في المنهج
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-lg shadow-sm border border-indigo-100">
                  <div className="text-lg font-semibold text-orange-600 mb-2">📝 محتوى مُضاف</div>
                  <div className="text-2xl font-bold text-orange-500">
                    {comparisonResult.added_content?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">إضافات جديدة</div>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-indigo-100">
                  <div className="text-lg font-semibold text-blue-600 mb-2">❓ أسئلة محدثة</div>
                  <div className="text-2xl font-bold text-blue-500">
                    {comparisonResult.questions_changes?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">تحديثات الأسئلة</div>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-indigo-100">
                  <div className="text-lg font-semibold text-red-600 mb-2">🚨 تغييرات رئيسية</div>
                  <div className="text-2xl font-bold text-red-500">
                    {comparisonResult.major_differences?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600">اختلافات مهمة</div>
                </div>
              </div>
            </div>

            {/* محتوى مُضاف - الأهم للمعلمين */}
            {comparisonResult.added_content && comparisonResult.added_content.length > 0 && (
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-xl border-2 border-green-200 mb-6">
                <h4 className="text-xl font-bold text-green-800 mb-4 flex items-center gap-2">
                  ➕ المحتوى الجديد المُضاف للمنهج ({comparisonResult.added_content.length})
                  <Badge className="bg-green-600 text-white">جديد!</Badge>
                </h4>
                <div className="space-y-3">
                  {comparisonResult.added_content.map((content, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg shadow-sm border border-green-100">
                      <div className="flex items-start gap-3">
                        <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mt-0.5">
                          {index + 1}
                        </span>
                        <div className="flex-1">
                          <p className="text-green-800 font-medium">{content}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* تغييرات الأسئلة - مهم للمعلمين */}
            {comparisonResult.questions_changes && comparisonResult.questions_changes.length > 0 && (
              <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-6 rounded-xl border-2 border-blue-200 mb-6">
                <h4 className="text-xl font-bold text-blue-800 mb-4 flex items-center gap-2">
                  ❓ تحديثات الأسئلة والتمارين ({comparisonResult.questions_changes.length})
                  <Badge className="bg-blue-600 text-white">محدث!</Badge>
                </h4>
                <div className="space-y-3">
                  {comparisonResult.questions_changes.map((change, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg shadow-sm border border-blue-100">
                      <div className="flex items-start gap-3">
                        <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mt-0.5">
                          {index + 1}
                        </span>
                        <div className="flex-1">
                          <p className="text-blue-800 font-medium">{change}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* تغييرات المحتوى العام */}
            {comparisonResult.content_changes && comparisonResult.content_changes.length > 0 && (
              <div className="bg-gradient-to-r from-orange-50 to-amber-50 p-6 rounded-xl border-2 border-orange-200 mb-6">
                <h4 className="text-xl font-bold text-orange-800 mb-4 flex items-center gap-2">
                  � تحديثات المحتوى العام ({comparisonResult.content_changes.length})
                </h4>
                <div className="space-y-3">
                  {comparisonResult.content_changes.slice(0, 8).map((change, index) => (
                    <div key={index} className="bg-white p-3 rounded-lg shadow-sm border border-orange-100">
                      <div className="flex items-start gap-3">
                        <span className="bg-orange-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mt-0.5">
                          {index + 1}
                        </span>
                        <p className="text-orange-800 text-sm">{change}</p>
                      </div>
                    </div>
                  ))}
                  {comparisonResult.content_changes.length > 8 && (
                    <div className="text-center">
                      <Badge variant="outline" className="border-orange-300 text-orange-600">
                        ... و {comparisonResult.content_changes.length - 8} تغيير إضافي
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* اختلافات رئيسية - تحتاج انتباه */}
            {comparisonResult.major_differences && comparisonResult.major_differences.length > 0 && (
              <div className="bg-gradient-to-r from-red-50 to-pink-50 p-6 rounded-xl border-2 border-red-200 mb-6">
                <h4 className="text-xl font-bold text-red-800 mb-4 flex items-center gap-2">
                  🚨 اختلافات رئيسية تحتاج انتباه ({comparisonResult.major_differences.length})
                  <Badge className="bg-red-600 text-white">مهم!</Badge>
                </h4>
                <div className="space-y-3">
                  {comparisonResult.major_differences.map((diff, index) => (
                    <div key={index} className="bg-white p-4 rounded-lg shadow-sm border border-red-100">
                      <div className="flex items-start gap-3">
                        <span className="bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mt-0.5">
                          ⚠
                        </span>
                        <div className="flex-1">
                          <p className="text-red-800 font-medium">{diff}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* محتوى مُحذوف */}
            {comparisonResult.removed_content && comparisonResult.removed_content.length > 0 && (
              <div className="bg-gradient-to-r from-gray-50 to-slate-50 p-6 rounded-xl border-2 border-gray-200 mb-6">
                <h4 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  ➖ محتوى مُحذوف من المنهج ({comparisonResult.removed_content.length})
                </h4>
                <div className="space-y-3">
                  {comparisonResult.removed_content.slice(0, 5).map((content, index) => (
                    <div key={index} className="bg-white p-3 rounded-lg shadow-sm border border-gray-100">
                      <div className="flex items-start gap-3">
                        <span className="bg-gray-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mt-0.5">
                          {index + 1}
                        </span>
                        <p className="text-gray-700 text-sm line-through opacity-70">{content}</p>
                      </div>
                    </div>
                  ))}
                  {comparisonResult.removed_content.length > 5 && (
                    <div className="text-center">
                      <Badge variant="outline" className="border-gray-300 text-gray-600">
                        ... و {comparisonResult.removed_content.length - 5} حذف إضافي
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Summary and Recommendation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                  📋 ملخص التحليل
                </h4>
                <p className="text-blue-700 text-sm whitespace-pre-wrap">
                  {comparisonResult.summary || 'لا يوجد ملخص متاح'}
                </p>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold text-green-800 mb-2 flex items-center gap-2">
                  💡 التوصيات
                </h4>
                <p className="text-green-700 text-sm whitespace-pre-wrap">
                  {comparisonResult.recommendation || 'لا توجد توصيات متاحة'}
                </p>
              </div>
            </div>

            {/* Detailed Analysis */}
            {comparisonResult.detailed_analysis && (
              <details className="mt-4">
                <summary className="cursor-pointer font-semibold text-gray-700 hover:text-gray-900 flex items-center gap-2">
                  🔍 التحليل المفصل
                </summary>
                <div className="mt-3 p-4 bg-gray-50 rounded-lg">
                  <p className="text-gray-700 text-sm whitespace-pre-wrap">
                    {comparisonResult.detailed_analysis}
                  </p>
                </div>
              </details>
            )}
          </CardContent>
        </Card>
      )}

      {/* Visual Comparison Results - Secondary */}
      {visualComparisonResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              🖼️ نتائج المقارنة البصرية المحسنة
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Overall Score */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {formatNumber(visualComparisonResult.similarity_score, 1)}%
                </div>
                <div className="text-gray-600">نسبة التطابق البصري</div>
                <div className={`mt-2 px-3 py-1 rounded-full text-sm inline-block ${
                  visualComparisonResult.probable_content_match 
                    ? 'bg-green-100 text-green-800' 
                    : visualComparisonResult.major_changes_detected
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {visualComparisonResult.probable_content_match 
                    ? '✅ محتوى متطابق تقريباً' 
                    : visualComparisonResult.major_changes_detected
                    ? '⚠️ تغييرات كبيرة مكتشفة'
                    : '🔍 اختلافات متوسطة'}
                </div>
              </div>

              {/* Key Metrics Only */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded">
                  <div className="font-bold text-blue-600">{formatNumber(visualComparisonResult.ssim_score * 100, 1)}%</div>
                  <div className="text-sm text-gray-600">SSIM</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded">
                  <div className="font-bold text-green-600">{formatNumber(visualComparisonResult.phash_score * 100, 1)}%</div>
                  <div className="text-sm text-gray-600">pHash</div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded">
                  <div className="font-bold text-purple-600">{visualComparisonResult.changed_regions.length}</div>
                  <div className="text-sm text-gray-600">مناطق متغيرة</div>
                </div>
              </div>

              {/* Compact Analysis */}
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-blue-700 text-sm">{visualComparisonResult.analysis_summary}</p>
              </div>

              {/* Technical Details - Collapsed by default */}
              <details>
                <summary className="cursor-pointer font-semibold text-gray-700 hover:text-gray-900">
                  🔧 تفاصيل تقنية إضافية
                </summary>
                <div className="mt-2 p-3 bg-gray-50 rounded text-sm space-y-1">
                  <div>وقت المعالجة: <span className="font-mono">{formatNumber(visualComparisonResult.processing_time, 2)}s</span></div>
                  <div>MSE: <span className="font-mono">{formatNumber(visualComparisonResult.mean_squared_error, 2)}</span></div>
                  <div>PSNR: <span className="font-mono">{formatNumber(visualComparisonResult.peak_signal_noise_ratio, 2)} dB</span></div>
                </div>
              </details>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Rest of existing UI ... */}
    </div>
  );
}
