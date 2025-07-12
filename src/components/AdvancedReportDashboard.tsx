import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { 
  FileText, 
  Brain, 
  Eye, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  TrendingUp,
  BarChart3,
  FileImage,
  Zap,
  Download,
  RefreshCw
} from 'lucide-react';

interface ProcessingStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  duration?: number;
  details?: string;
  icon: React.ReactNode;
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
}

interface AdvancedReportProps {
  sessionId: string;
  oldImageResult?: OCRResult;
  newImageResult?: OCRResult;
  comparisonResult?: ComparisonResult;
  isProcessing: boolean;
  onRetry?: () => void;
  onDownloadReport?: () => void;
}

const AdvancedReportDashboard: React.FC<AdvancedReportProps> = ({
  sessionId,
  oldImageResult,
  newImageResult,
  comparisonResult,
  isProcessing,
  onRetry,
  onDownloadReport
}) => {
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([
    {
      id: 'upload',
      name: 'رفع الملفات',
      status: 'completed',
      progress: 100,
      icon: <FileImage className="w-4 h-4" />
    },
    {
      id: 'ocr_old',
      name: 'استخراج النص من الصورة القديمة',
      status: oldImageResult ? 'completed' : (isProcessing ? 'processing' : 'pending'),
      progress: oldImageResult ? 100 : (isProcessing ? 65 : 0),
      duration: oldImageResult?.processing_time,
      icon: <Eye className="w-4 h-4" />
    },
    {
      id: 'ocr_new',
      name: 'استخراج النص من الصورة الجديدة',
      status: newImageResult ? 'completed' : (isProcessing ? 'processing' : 'pending'),
      progress: newImageResult ? 100 : (isProcessing ? 65 : 0),
      duration: newImageResult?.processing_time,
      icon: <Eye className="w-4 h-4" />
    },
    {
      id: 'ai_analysis',
      name: 'التحليل بالذكاء الاصطناعي',
      status: comparisonResult ? 'completed' : (isProcessing ? 'processing' : 'pending'),
      progress: comparisonResult ? 100 : (isProcessing ? 80 : 0),
      duration: comparisonResult?.processing_time,
      icon: <Brain className="w-4 h-4" />
    },
    {
      id: 'report',
      name: 'إنشاء التقرير النهائي',
      status: comparisonResult ? 'completed' : 'pending',
      progress: comparisonResult ? 100 : 0,
      icon: <FileText className="w-4 h-4" />
    }
  ]);

  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    // محاكاة تحديث السجلات
    if (isProcessing) {
      const interval = setInterval(() => {
        const newLog = `[${new Date().toLocaleTimeString('ar-SA')}] جاري معالجة البيانات...`;
        setLogs(prev => [...prev.slice(-20), newLog]); // الاحتفاظ بآخر 20 سجل
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isProcessing]);

  const getStepStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'processing': return 'bg-blue-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-300';
    }
  };

  const getStepStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'processing': return <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-600" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const totalProcessingTime = processingSteps
    .filter(step => step.duration)
    .reduce((sum, step) => sum + (step.duration || 0), 0);

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">تقرير المقارنة المتقدم</h1>
          <p className="text-gray-600 mt-2">معرف الجلسة: {sessionId}</p>
        </div>
        <div className="flex gap-2">
          {onRetry && (
            <Button variant="outline" onClick={onRetry} disabled={isProcessing}>
              <RefreshCw className="w-4 h-4 mr-2" />
              إعادة المحاولة
            </Button>
          )}
          {onDownloadReport && comparisonResult && (
            <Button onClick={onDownloadReport}>
              <Download className="w-4 h-4 mr-2" />
              تحميل التقرير
            </Button>
          )}
        </div>
      </div>

      {/* Processing Steps */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            مراحل المعالجة
          </CardTitle>
          <CardDescription>
            تتبع مراحل معالجة الصور والتحليل في الوقت الفعلي
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {processingSteps.map((step, index) => (
              <div key={step.id} className="flex items-center gap-4 p-4 border rounded-lg">
                <div className="flex items-center gap-3 flex-1">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getStepStatusColor(step.status)}`}>
                    <span className="text-white text-sm font-bold">{index + 1}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      {step.icon}
                      <span className="font-medium">{step.name}</span>
                      {getStepStatusIcon(step.status)}
                    </div>
                    <Progress value={step.progress} className="mt-2 h-2" />
                    {step.duration && (
                      <p className="text-sm text-gray-500 mt-1">
                        وقت المعالجة: {step.duration.toFixed(2)} ثانية
                      </p>
                    )}
                  </div>
                </div>
                <Badge variant={step.status === 'completed' ? 'default' : 'secondary'}>
                  {step.progress}%
                </Badge>
              </div>
            ))}
          </div>
          
          {totalProcessingTime > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                إجمالي وقت المعالجة: {totalProcessingTime.toFixed(2)} ثانية
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">نظرة عامة</TabsTrigger>
          <TabsTrigger value="ocr">استخراج النص</TabsTrigger>
          <TabsTrigger value="comparison">المقارنة</TabsTrigger>
          <TabsTrigger value="analysis">التحليل المفصل</TabsTrigger>
          <TabsTrigger value="logs">السجلات</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  نسبة التشابه
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">
                  {comparisonResult ? `${comparisonResult.similarity_percentage}%` : '--'}
                </div>
                <Progress 
                  value={comparisonResult?.similarity_percentage || 0} 
                  className="mt-2" 
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  دقة الاستخراج
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">
                  {oldImageResult && newImageResult 
                    ? `${Math.round((oldImageResult.confidence + newImageResult.confidence) / 2 * 100)}%`
                    : '--'
                  }
                </div>
                <p className="text-sm text-gray-600 mt-1">متوسط دقة OCR</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  وقت المعالجة
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-600">
                  {totalProcessingTime > 0 ? `${totalProcessingTime.toFixed(1)}s` : '--'}
                </div>
                <p className="text-sm text-gray-600 mt-1">إجمالي الوقت</p>
              </CardContent>
            </Card>
          </div>

          {comparisonResult && (
            <Card>
              <CardHeader>
                <CardTitle>ملخص المقارنة</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 leading-relaxed">{comparisonResult.summary}</p>
                <Separator className="my-4" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold text-green-700 mb-2">المحتوى المضاف</h4>
                    <ul className="text-sm space-y-1">
                      {comparisonResult.added_content.slice(0, 3).map((item, idx) => (
                        <li key={idx} className="text-green-600">• {item}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-red-700 mb-2">المحتوى المحذوف</h4>
                    <ul className="text-sm space-y-1">
                      {comparisonResult.removed_content.slice(0, 3).map((item, idx) => (
                        <li key={idx} className="text-red-600">• {item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* OCR Tab */}
        <TabsContent value="ocr" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {oldImageResult && (
              <Card>
                <CardHeader>
                  <CardTitle>الصورة القديمة</CardTitle>
                  <CardDescription>نتائج استخراج النص</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>دقة الاستخراج:</span>
                    <Badge variant="outline">{Math.round(oldImageResult.confidence * 100)}%</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>عدد الكلمات:</span>
                    <span className="font-mono">{oldImageResult.word_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>عدد الأحرف:</span>
                    <span className="font-mono">{oldImageResult.character_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>وقت المعالجة:</span>
                    <span className="font-mono">{oldImageResult.processing_time.toFixed(2)}s</span>
                  </div>
                  <Separator />
                  <div>
                    <h4 className="font-semibold mb-2">معاينة النص:</h4>
                    <ScrollArea className="h-32 w-full border rounded p-2">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {oldImageResult.text.substring(0, 300)}...
                      </p>
                    </ScrollArea>
                  </div>
                </CardContent>
              </Card>
            )}

            {newImageResult && (
              <Card>
                <CardHeader>
                  <CardTitle>الصورة الجديدة</CardTitle>
                  <CardDescription>نتائج استخراج النص</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>دقة الاستخراج:</span>
                    <Badge variant="outline">{Math.round(newImageResult.confidence * 100)}%</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>عدد الكلمات:</span>
                    <span className="font-mono">{newImageResult.word_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>عدد الأحرف:</span>
                    <span className="font-mono">{newImageResult.character_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>وقت المعالجة:</span>
                    <span className="font-mono">{newImageResult.processing_time.toFixed(2)}s</span>
                  </div>
                  <Separator />
                  <div>
                    <h4 className="font-semibold mb-2">معاينة النص:</h4>
                    <ScrollArea className="h-32 w-full border rounded p-2">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {newImageResult.text.substring(0, 300)}...
                      </p>
                    </ScrollArea>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Comparison Tab */}
        <TabsContent value="comparison" className="space-y-4">
          {comparisonResult ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>نتائج المقارنة</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {comparisonResult.similarity_percentage}%
                      </div>
                      <p className="text-sm text-gray-600">نسبة التشابه</p>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {comparisonResult.added_content.length}
                      </div>
                      <p className="text-sm text-gray-600">إضافات جديدة</p>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        {comparisonResult.removed_content.length}
                      </div>
                      <p className="text-sm text-gray-600">محتوى محذوف</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>التوصيات</CardTitle>
                </CardHeader>
                <CardContent>
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>توصية النظام</AlertTitle>
                    <AlertDescription>{comparisonResult.recommendation}</AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-500">لا توجد نتائج مقارنة متاحة بعد</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Detailed Analysis Tab */}
        <TabsContent value="analysis" className="space-y-4">
          {comparisonResult?.detailed_analysis ? (
            <Card>
              <CardHeader>
                <CardTitle>التحليل المفصل</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96 w-full">
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap text-sm">
                      {comparisonResult.detailed_analysis}
                    </pre>
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-500">التحليل المفصل غير متاح بعد</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                سجلات المعالجة
              </CardTitle>
              <CardDescription>تتبع مفصل لجميع عمليات المعالجة</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64 w-full border rounded p-4">
                <div className="space-y-1 font-mono text-sm">
                  {logs.length > 0 ? (
                    logs.map((log, index) => (
                      <div key={index} className="text-gray-700">{log}</div>
                    ))
                  ) : (
                    <p className="text-gray-500">لا توجد سجلات متاحة</p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedReportDashboard; 