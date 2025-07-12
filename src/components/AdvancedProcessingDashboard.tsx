import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Download, 
  FileText, 
  Image, 
  BarChart3, 
  Eye,
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
  Settings,
  RefreshCw,
  TrendingUp,
  Database,
  Layers,
  Monitor,
  Activity
} from 'lucide-react';

interface ProcessingStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  duration?: number;
  confidence?: number;
  details?: string;
  attempts?: number;
  maxAttempts?: number;
}

interface OCRAttempt {
  language: string;
  config: string;
  confidence: number;
  success: boolean;
  duration: number;
  textLength: number;
}

interface ProcessingResult {
  id: string;
  fileName: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  confidence: number;
  textLength: number;
  wordCount: number;
  processingTime: number;
  language: string;
  ocrAttempts: OCRAttempt[];
  extractedText: string;
  markdownContent: string;
  structuredAnalysis?: any;
}

interface ComparisonResult {
  id: string;
  oldFileId: string;
  newFileId: string;
  similarity: number;
  confidence: number;
  processingTime: number;
  changes: string[];
  summary: string;
  recommendation: string;
  detailedAnalysis: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

interface AdvancedProcessingDashboardProps {
  isProcessing: boolean;
  currentStep: string;
  progress: number;
  processingSteps: ProcessingStep[];
  oldResults: ProcessingResult[];
  newResults: ProcessingResult[];
  comparisons: ComparisonResult[];
  logs: string[];
  onBack: () => void;
  onRetry: () => void;
  onExportReport: () => void;
}

const AdvancedProcessingDashboard: React.FC<AdvancedProcessingDashboardProps> = ({
  isProcessing,
  currentStep,
  progress,
  processingSteps,
  oldResults,
  newResults,
  comparisons,
  logs,
  onBack,
  onRetry,
  onExportReport
}) => {
  const [selectedTab, setSelectedTab] = useState("overview");
  const [selectedResult, setSelectedResult] = useState<ProcessingResult | null>(null);
  const [selectedComparison, setSelectedComparison] = useState<ComparisonResult | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll logs
  useEffect(() => {
    if (autoScroll && logs.length > 0) {
      const logsContainer = document.getElementById('logs-container');
      if (logsContainer) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
      }
    }
  }, [logs, autoScroll]);

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { color: 'bg-gray-500', text: 'في الانتظار' },
      processing: { color: 'bg-blue-500', text: 'جاري المعالجة' },
      completed: { color: 'bg-green-500', text: 'مكتمل' },
      error: { color: 'bg-red-500', text: 'خطأ' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <Badge className={`${config.color} text-white text-xs`}>
        {config.text}
      </Badge>
    );
  };

  const totalFiles = oldResults.length + newResults.length;
  const completedFiles = [...oldResults, ...newResults].filter(r => r.status === 'completed').length;
  const avgConfidence = [...oldResults, ...newResults]
    .filter(r => r.status === 'completed')
    .reduce((acc, r) => acc + r.confidence, 0) / completedFiles || 0;

  if (isProcessing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
        <div className="container mx-auto px-6 py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">معالجة متقدمة بالذكاء الاصطناعي</h1>
              <p className="text-gray-600 mt-2">
                {currentStep} - التقدم: {Math.round(progress)}%
              </p>
            </div>
            <Button variant="outline" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 ml-2" />
              إيقاف المعالجة
            </Button>
          </div>

          {/* Progress Overview */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                التقدم الإجمالي
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>التقدم العام</span>
                    <span>{Math.round(progress)}%</span>
                  </div>
                  <Progress value={progress} className="h-3" />
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{totalFiles}</div>
                    <div className="text-sm text-gray-600">إجمالي الملفات</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{completedFiles}</div>
                    <div className="text-sm text-gray-600">ملفات مكتملة</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{Math.round(avgConfidence * 100)}%</div>
                    <div className="text-sm text-gray-600">متوسط الثقة</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{comparisons.length}</div>
                    <div className="text-sm text-gray-600">مقارنات</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Processing Steps */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="w-5 h-5" />
                خطوات المعالجة
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {processingSteps.map((step, index) => (
                  <div key={step.id} className="flex items-center gap-4">
                    <div className="flex-shrink-0">
                      {getStepIcon(step.status)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">{step.name}</span>
                        <div className="flex items-center gap-2">
                          {step.attempts && step.maxAttempts && (
                            <span className="text-xs text-gray-500">
                              {step.attempts}/{step.maxAttempts}
                            </span>
                          )}
                          {step.confidence && (
                            <Badge className={getConfidenceColor(step.confidence)}>
                              {Math.round(step.confidence * 100)}%
                            </Badge>
                          )}
                          {step.duration && (
                            <span className="text-xs text-gray-500">
                              {step.duration.toFixed(1)}ث
                            </span>
                          )}
                        </div>
                      </div>
                      {step.status === 'processing' && (
                        <Progress value={step.progress} className="h-2" />
                      )}
                      {step.details && (
                        <p className="text-sm text-gray-600 mt-1">{step.details}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Live Logs */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Monitor className="w-5 h-5" />
                  سجل المعالجة المباشر
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setAutoScroll(!autoScroll)}
                >
                  {autoScroll ? 'إيقاف التمرير' : 'تفعيل التمرير'}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea 
                id="logs-container"
                className="h-64 w-full border rounded-md p-4 bg-gray-50 font-mono text-sm"
              >
                {logs.length === 0 ? (
                  <p className="text-gray-500">لا توجد سجلات بعد...</p>
                ) : (
                  <div className="space-y-1">
                    {logs.slice(-50).map((log, index) => (
                      <div key={index} className="text-gray-700">
                        {log}
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Results view when processing is complete
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      {/* Header */}
      <header className="bg-white shadow-sm border-b p-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 ml-2" />
              العودة
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">نتائج المعالجة المتقدمة</h1>
              <p className="text-sm text-gray-600">
                تم معالجة {completedFiles} من {totalFiles} ملف بنجاح
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={onRetry} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 ml-2" />
              إعادة المعالجة
            </Button>
            <Button onClick={onExportReport} size="sm">
              <Download className="w-4 h-4 ml-2" />
              تصدير التقرير
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* Statistics Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{totalFiles}</div>
            <div className="text-sm text-gray-600">إجمالي الملفات</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{completedFiles}</div>
            <div className="text-sm text-gray-600">ملفات مكتملة</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{Math.round(avgConfidence * 100)}%</div>
            <div className="text-sm text-gray-600">متوسط الثقة</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">{comparisons.filter(c => c.status === 'completed').length}</div>
            <div className="text-sm text-gray-600">مقارنات مكتملة</div>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">نظرة عامة</TabsTrigger>
            <TabsTrigger value="ocr-results">نتائج OCR</TabsTrigger>
            <TabsTrigger value="comparisons">المقارنات</TabsTrigger>
            <TabsTrigger value="analysis">التحليل التفصيلي</TabsTrigger>
            <TabsTrigger value="logs">السجلات</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Processing Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    ملخص المعالجة
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {processingSteps.map((step) => (
                      <div key={step.id} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStepIcon(step.status)}
                          <span className="text-sm">{step.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {step.confidence && (
                            <Badge className={getConfidenceColor(step.confidence)}>
                              {Math.round(step.confidence * 100)}%
                            </Badge>
                          )}
                          {step.duration && (
                            <span className="text-xs text-gray-500">
                              {step.duration.toFixed(1)}ث
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Quality Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    مقاييس الجودة
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>متوسط ثقة OCR</span>
                        <span>{Math.round(avgConfidence * 100)}%</span>
                      </div>
                      <Progress value={avgConfidence * 100} className="h-2" />
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>معدل النجاح</span>
                        <span>{Math.round((completedFiles / totalFiles) * 100)}%</span>
                      </div>
                      <Progress value={(completedFiles / totalFiles) * 100} className="h-2" />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <div className="text-center">
                        <div className="text-lg font-bold text-blue-600">
                          {[...oldResults, ...newResults]
                            .filter(r => r.status === 'completed')
                            .reduce((acc, r) => acc + r.wordCount, 0)}
                        </div>
                        <div className="text-xs text-gray-600">إجمالي الكلمات</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-600">
                          {[...oldResults, ...newResults]
                            .filter(r => r.status === 'completed')
                            .reduce((acc, r) => acc + r.processingTime, 0)
                            .toFixed(1)}ث
                        </div>
                        <div className="text-xs text-gray-600">إجمالي وقت المعالجة</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="ocr-results" className="mt-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Old Files Results */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-600">
                    <FileText className="w-5 h-5" />
                    الكتاب القديم ({oldResults.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-96">
                    {oldResults.map((result) => (
                      <div
                        key={result.id}
                        className={`p-3 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                          selectedResult?.id === result.id ? 'bg-orange-50 border-r-4 border-r-orange-500' : ''
                        }`}
                        onClick={() => setSelectedResult(result)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium truncate">{result.fileName}</div>
                          {getStatusBadge(result.status)}
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                          <div>ثقة: {Math.round(result.confidence * 100)}%</div>
                          <div>كلمات: {result.wordCount}</div>
                          <div>لغة: {result.language}</div>
                          <div>وقت: {result.processingTime.toFixed(1)}ث</div>
                        </div>
                        {result.ocrAttempts && result.ocrAttempts.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs text-gray-500">
                              محاولات OCR: {result.ocrAttempts.length}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* New Files Results */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-blue-600">
                    <FileText className="w-5 h-5" />
                    الكتاب الجديد ({newResults.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-96">
                    {newResults.map((result) => (
                      <div
                        key={result.id}
                        className={`p-3 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                          selectedResult?.id === result.id ? 'bg-blue-50 border-r-4 border-r-blue-500' : ''
                        }`}
                        onClick={() => setSelectedResult(result)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium truncate">{result.fileName}</div>
                          {getStatusBadge(result.status)}
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                          <div>ثقة: {Math.round(result.confidence * 100)}%</div>
                          <div>كلمات: {result.wordCount}</div>
                          <div>لغة: {result.language}</div>
                          <div>وقت: {result.processingTime.toFixed(1)}ث</div>
                        </div>
                        {result.ocrAttempts && result.ocrAttempts.length > 0 && (
                          <div className="mt-2">
                            <div className="text-xs text-gray-500">
                              محاولات OCR: {result.ocrAttempts.length}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Selected Result Details */}
            {selectedResult && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>تفاصيل الملف: {selectedResult.fileName}</CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="text">
                    <TabsList>
                      <TabsTrigger value="text">النص المستخرج</TabsTrigger>
                      <TabsTrigger value="attempts">محاولات OCR</TabsTrigger>
                      <TabsTrigger value="analysis">التحليل</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="text" className="mt-4">
                      <ScrollArea className="h-64 w-full border rounded-md p-4 bg-gray-50">
                        <pre className="text-sm whitespace-pre-wrap">
                          {selectedResult.extractedText || 'لا يوجد نص مستخرج'}
                        </pre>
                      </ScrollArea>
                    </TabsContent>
                    
                    <TabsContent value="attempts" className="mt-4">
                      {selectedResult.ocrAttempts && selectedResult.ocrAttempts.length > 0 ? (
                        <div className="space-y-3">
                          {selectedResult.ocrAttempts.map((attempt, index) => (
                            <Card key={index} className="p-3">
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                                <div><strong>اللغة:</strong> {attempt.language}</div>
                                <div><strong>الثقة:</strong> {Math.round(attempt.confidence * 100)}%</div>
                                <div><strong>الوقت:</strong> {attempt.duration.toFixed(1)}ث</div>
                                <div><strong>طول النص:</strong> {attempt.textLength}</div>
                              </div>
                              <div className="mt-2 text-xs text-gray-600">
                                <strong>الإعدادات:</strong> {attempt.config}
                              </div>
                            </Card>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500">لا توجد تفاصيل محاولات OCR</p>
                      )}
                    </TabsContent>
                    
                    <TabsContent value="analysis" className="mt-4">
                      {selectedResult.structuredAnalysis ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div><strong>الموضوع:</strong> {selectedResult.structuredAnalysis.subject}</div>
                            <div><strong>المستوى:</strong> {selectedResult.structuredAnalysis.grade_level}</div>
                            <div><strong>الفصل:</strong> {selectedResult.structuredAnalysis.chapter_title}</div>
                            <div><strong>الصعوبة:</strong> {selectedResult.structuredAnalysis.difficulty_level}</div>
                          </div>
                          
                          {selectedResult.structuredAnalysis.learning_objectives && (
                            <div>
                              <strong>الأهداف التعليمية:</strong>
                              <ul className="list-disc list-inside mt-1 text-sm">
                                {selectedResult.structuredAnalysis.learning_objectives.map((obj: string, i: number) => (
                                  <li key={i}>{obj}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-gray-500">لا يوجد تحليل منظم متاح</p>
                      )}
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="comparisons" className="mt-6">
            <div className="space-y-6">
              {comparisons.length > 0 ? (
                comparisons.map((comparison) => (
                  <Card key={comparison.id} className="cursor-pointer hover:shadow-md transition-shadow"
                        onClick={() => setSelectedComparison(comparison)}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">
                          مقارنة: {comparison.oldFileId} ↔ {comparison.newFileId}
                        </CardTitle>
                        {getStatusBadge(comparison.status)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-purple-600">{comparison.similarity}%</div>
                          <div className="text-sm text-gray-600">نسبة التشابه</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">{Math.round(comparison.confidence * 100)}%</div>
                          <div className="text-sm text-gray-600">ثقة التحليل</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-orange-600">{comparison.changes.length}</div>
                          <div className="text-sm text-gray-600">عدد التغييرات</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">{comparison.processingTime.toFixed(1)}ث</div>
                          <div className="text-sm text-gray-600">وقت المعالجة</div>
                        </div>
                      </div>
                      
                      {comparison.summary && (
                        <div className="mt-4 p-3 bg-gray-50 rounded-md">
                          <p className="text-sm"><strong>الملخص:</strong> {comparison.summary}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <p className="text-gray-500">لا توجد مقارنات متاحة بعد</p>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Selected Comparison Details */}
            {selectedComparison && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>تفاصيل المقارنة</CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="summary">
                    <TabsList>
                      <TabsTrigger value="summary">الملخص</TabsTrigger>
                      <TabsTrigger value="changes">التغييرات</TabsTrigger>
                      <TabsTrigger value="analysis">التحليل التفصيلي</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="summary" className="mt-4">
                      <div className="space-y-4">
                        <Alert>
                          <AlertDescription>
                            <strong>التوصية:</strong> {selectedComparison.recommendation}
                          </AlertDescription>
                        </Alert>
                        <p>{selectedComparison.summary}</p>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="changes" className="mt-4">
                      <div className="space-y-2">
                        {selectedComparison.changes.length > 0 ? (
                          selectedComparison.changes.map((change, index) => (
                            <div key={index} className="p-3 border-l-4 border-l-blue-500 bg-blue-50">
                              {change}
                            </div>
                          ))
                        ) : (
                          <p className="text-gray-500">لا توجد تغييرات محددة</p>
                        )}
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="analysis" className="mt-4">
                      <ScrollArea className="h-64 w-full border rounded-md p-4 bg-gray-50">
                        <pre className="text-sm whitespace-pre-wrap">
                          {selectedComparison.detailedAnalysis || 'لا يوجد تحليل تفصيلي متاح'}
                        </pre>
                      </ScrollArea>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="analysis" className="mt-6">
            <div className="grid lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>تحليل الأداء</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">توزيع مستويات الثقة</h4>
                      <div className="space-y-2">
                        {[
                          { label: 'عالية (80%+)', count: [...oldResults, ...newResults].filter(r => r.confidence >= 0.8).length, color: 'bg-green-500' },
                          { label: 'متوسطة (60-79%)', count: [...oldResults, ...newResults].filter(r => r.confidence >= 0.6 && r.confidence < 0.8).length, color: 'bg-yellow-500' },
                          { label: 'منخفضة (<60%)', count: [...oldResults, ...newResults].filter(r => r.confidence < 0.6).length, color: 'bg-red-500' }
                        ].map((item) => (
                          <div key={item.label} className="flex items-center gap-2">
                            <div className={`w-4 h-4 rounded ${item.color}`}></div>
                            <span className="text-sm">{item.label}: {item.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">إحصائيات اللغات</h4>
                      <div className="space-y-1 text-sm">
                        {Object.entries(
                          [...oldResults, ...newResults]
                            .filter(r => r.status === 'completed')
                            .reduce((acc, r) => {
                              acc[r.language] = (acc[r.language] || 0) + 1;
                              return acc;
                            }, {} as Record<string, number>)
                        ).map(([lang, count]) => (
                          <div key={lang} className="flex justify-between">
                            <span>{lang}</span>
                            <span>{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>ملخص التحليل التعليمي</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">المواد الدراسية</h4>
                      <div className="space-y-1 text-sm">
                        {Object.entries(
                          [...oldResults, ...newResults]
                            .filter(r => r.structuredAnalysis?.subject)
                            .reduce((acc, r) => {
                              const subject = r.structuredAnalysis.subject;
                              acc[subject] = (acc[subject] || 0) + 1;
                              return acc;
                            }, {} as Record<string, number>)
                        ).map(([subject, count]) => (
                          <div key={subject} className="flex justify-between">
                            <span>{subject}</span>
                            <span>{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">مستويات الصعوبة</h4>
                      <div className="space-y-1 text-sm">
                        {Object.entries(
                          [...oldResults, ...newResults]
                            .filter(r => r.structuredAnalysis?.difficulty_level)
                            .reduce((acc, r) => {
                              const level = r.structuredAnalysis.difficulty_level;
                              acc[level] = (acc[level] || 0) + 1;
                              return acc;
                            }, {} as Record<string, number>)
                        ).map(([level, count]) => (
                          <div key={level} className="flex justify-between">
                            <span>{level}</span>
                            <span>{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="logs" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-5 h-5" />
                    سجل المعالجة الكامل
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{logs.length} سجل</Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setAutoScroll(!autoScroll)}
                    >
                      {autoScroll ? 'إيقاف التمرير' : 'تفعيل التمرير'}
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea 
                  id="logs-container"
                  className="h-96 w-full border rounded-md p-4 bg-gray-50 font-mono text-sm"
                >
                  {logs.length === 0 ? (
                    <p className="text-gray-500">لا توجد سجلات متاحة</p>
                  ) : (
                    <div className="space-y-1">
                      {logs.map((log, index) => (
                        <div key={index} className={`${
                          log.includes('❌') ? 'text-red-600' :
                          log.includes('✅') ? 'text-green-600' :
                          log.includes('⚠️') ? 'text-yellow-600' :
                          log.includes('🔍') || log.includes('📝') ? 'text-blue-600' :
                          'text-gray-700'
                        }`}>
                          {log}
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdvancedProcessingDashboard; 