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
  RefreshCw,
  FileDown
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
  common_words_count?: number; // Added for new UI
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

  const exportToMarkdown = () => {
    if (!comparisonResult) return;
    
    const markdown = `# تقرير المقارنة المتقدم
**معرف الجلسة:** ${sessionId}
**تاريخ التحليل:** ${new Date().toLocaleString('ar-SA')}

## 🎯 التحليل الذكي بواسطة Gemini AI

### 📝 ملخص التحليل
${comparisonResult.summary}

### 💡 التوصيات
${comparisonResult.recommendation}

### 🎯 درجة الثقة
${Math.round(comparisonResult.confidence_score * 100)}%

## 📊 نسبة التشابه النصي
**${comparisonResult.similarity_percentage}%**

### إحصائيات النص
- أحرف النص القديم: ${oldImageResult?.character_count || 0}
- أحرف النص الجديد: ${newImageResult?.character_count || 0}
- كلمات مشتركة: ${comparisonResult.common_words_count || 0}

## 🔍 الأسئلة والإضافات الجديدة

### 📝 محتوى مُضاف (${comparisonResult.added_content.length})
${comparisonResult.added_content.map(item => `- ${item}`).join('\n')}

### ❓ أسئلة محدثة (${comparisonResult.questions_changes.length})
${comparisonResult.questions_changes.map(item => `- ${item}`).join('\n')}

### 🚨 تغييرات رئيسية تحتاج انتباه (${comparisonResult.major_differences.length})
${comparisonResult.major_differences.map(item => `- ${item}`).join('\n')}

## 📋 معلومات المعالجة
- دقة الاستخراج: ${oldImageResult && newImageResult ? Math.round((oldImageResult.confidence + newImageResult.confidence) / 2 * 100) : 0}%
- ثقة التحليل: ${Math.round(comparisonResult.confidence_score * 100)}%
- وقت المعالجة: ${totalProcessingTime.toFixed(1)}s

## 🔍 التحليل المفصل
${comparisonResult.detailed_analysis}
`;

    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `تقرير_المقارنة_${sessionId}_${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportToHTML = () => {
    if (!comparisonResult) return;
    
    const html = `<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير المقارنة المتقدم</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }
        h2 { color: #1e40af; margin-top: 30px; }
        h3 { color: #1e3a8a; }
        .highlight { background: #dbeafe; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #059669; }
        .changes-list { background: #fef3c7; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .changes-list ul { margin: 10px 0; }
        .changes-list li { margin: 5px 0; }
        .gemini-analysis { background: #dbeafe; padding: 20px; border-radius: 10px; border-left: 5px solid #2563eb; }
        .similarity-box { background: #d1fae5; padding: 20px; border-radius: 10px; text-align: center; }
        .similarity-number { font-size: 4em; font-weight: bold; color: #059669; }
        .warning-box { background: #fed7d7; padding: 15px; border-radius: 8px; border-left: 5px solid #e53e3e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 تقرير المقارنة المتقدم</h1>
        <p><strong>معرف الجلسة:</strong> ${sessionId}</p>
        <p><strong>تاريخ التحليل:</strong> ${new Date().toLocaleString('ar-SA')}</p>
        
        <div class="gemini-analysis">
            <h2>🧠 التحليل الذكي بواسطة Gemini AI</h2>
            <div class="highlight">
                <h3>📝 ملخص التحليل</h3>
                <p>${comparisonResult.summary}</p>
            </div>
            <div class="highlight">
                <h3>💡 التوصيات</h3>
                <p>${comparisonResult.recommendation}</p>
            </div>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-number">${Math.round(comparisonResult.confidence_score * 100)}%</div>
                    <div>درجة الثقة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${comparisonResult.processing_time.toFixed(1)}s</div>
                    <div>وقت التحليل</div>
                </div>
            </div>
        </div>
        
        <div class="similarity-box">
            <h2>📊 نسبة التشابه النصي</h2>
            <div class="similarity-number">${comparisonResult.similarity_percentage}%</div>
            <p>Landing AI → Gemini</p>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-number">${oldImageResult?.character_count || 0}</div>
                    <div>أحرف النص القديم</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${newImageResult?.character_count || 0}</div>
                    <div>أحرف النص الجديد</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${comparisonResult.common_words_count || 0}</div>
                    <div>كلمات مشتركة</div>
                </div>
            </div>
        </div>
        
        <h2>🔍 الأسئلة والإضافات الجديدة</h2>
        
        <div class="changes-list">
            <h3>📝 محتوى مُضاف (${comparisonResult.added_content.length})</h3>
            <ul>
                ${comparisonResult.added_content.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>
        
        <div class="changes-list">
            <h3>❓ أسئلة محدثة (${comparisonResult.questions_changes.length})</h3>
            <ul>
                ${comparisonResult.questions_changes.map(item => `<li>${item}</li>`).join('')}
            </ul>
        </div>
        
        <div class="warning-box">
            <h3>🚨 تغييرات رئيسية تحتاج انتباه (${comparisonResult.major_differences.length})</h3>
            <ul>
                ${comparisonResult.major_differences.map(item => `<li><strong>${item}</strong></li>`).join('')}
            </ul>
        </div>
        
        <h2>📋 معلومات المعالجة</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-number">${oldImageResult && newImageResult ? Math.round((oldImageResult.confidence + newImageResult.confidence) / 2 * 100) : 0}%</div>
                <div>دقة الاستخراج</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${Math.round(comparisonResult.confidence_score * 100)}%</div>
                <div>ثقة التحليل</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${totalProcessingTime.toFixed(1)}s</div>
                <div>وقت المعالجة</div>
            </div>
        </div>
        
        <h2>🔍 التحليل المفصل</h2>
        <div class="highlight">
            <pre style="white-space: pre-wrap; font-family: monospace; font-size: 0.9em;">${comparisonResult.detailed_analysis}</pre>
        </div>
    </div>
</body>
</html>`;

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `تقرير_المقارنة_${sessionId}_${new Date().toISOString().split('T')[0]}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

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
          {comparisonResult && (
            <>
              <Button variant="outline" onClick={exportToMarkdown}>
                <FileDown className="w-4 h-4 mr-2" />
                تصدير MD
              </Button>
              <Button variant="outline" onClick={exportToHTML}>
                <FileDown className="w-4 h-4 mr-2" />
                تصدير HTML
              </Button>
            </>
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
          {/* Gemini Analysis - Top Priority */}
          {comparisonResult && (
            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-800">
                  <Brain className="w-6 h-6" />
                  🎯 التحليل الذكي بواسطة Gemini AI
                </CardTitle>
                <CardDescription className="text-blue-700">
                  التحليل الأساسي والتوصيات الذكية
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-blue-800 mb-2">📝 ملخص التحليل</h4>
                  <p className="text-gray-700 leading-relaxed">{comparisonResult.summary}</p>
                </div>
                
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-blue-800 mb-2">💡 التوصيات</h4>
                  <p className="text-gray-700 leading-relaxed">{comparisonResult.recommendation}</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-4 rounded-lg border">
                    <h4 className="font-semibold text-blue-800 mb-2">🎯 درجة الثقة</h4>
                    <div className="flex items-center gap-2">
                      <div className="text-2xl font-bold text-blue-600">
                        {Math.round(comparisonResult.confidence_score * 100)}%
                      </div>
                      <Progress value={comparisonResult.confidence_score * 100} className="flex-1" />
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border">
                    <h4 className="font-semibold text-blue-800 mb-2">⏱️ وقت التحليل</h4>
                    <div className="text-2xl font-bold text-blue-600">
                      {comparisonResult.processing_time.toFixed(1)}s
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Similarity Percentage */}
          <Card className="border-2 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-800">
                <TrendingUp className="w-6 h-6" />
                📊 نسبة التشابه النصي
              </CardTitle>
              <CardDescription className="text-green-700">
                Landing AI → Gemini
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <div className="text-6xl font-bold text-green-600 mb-4">
                {comparisonResult ? `${comparisonResult.similarity_percentage}%` : '--'}
              </div>
              <Progress 
                value={comparisonResult?.similarity_percentage || 0} 
                className="mb-4 h-4" 
              />
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="font-semibold text-gray-700">
                    {oldImageResult?.character_count || 0}
                  </div>
                  <div className="text-gray-500">أحرف النص القديم</div>
                </div>
                <div>
                  <div className="font-semibold text-gray-700">
                    {newImageResult?.character_count || 0}
                  </div>
                  <div className="text-gray-500">أحرف النص الجديد</div>
                </div>
                <div>
                  <div className="font-semibold text-gray-700">
                    {comparisonResult?.common_words_count || 0}
                  </div>
                  <div className="text-gray-500">كلمات مشتركة</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Questions and Additions Box */}
          {comparisonResult && (
            <Card className="border-2 border-orange-200 bg-orange-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-800">
                  <AlertCircle className="w-6 h-6" />
                  🔍 الأسئلة والإضافات الجديدة
                </CardTitle>
                <CardDescription className="text-orange-700">
                  التحديثات والتغييرات المهمة
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-4 rounded-lg border">
                    <h4 className="font-semibold text-green-700 mb-2 flex items-center gap-2">
                      <span className="text-2xl">{comparisonResult.added_content.length}</span>
                      📝 محتوى مُضاف
                    </h4>
                    <ul className="text-sm space-y-1 max-h-32 overflow-y-auto">
                      {comparisonResult.added_content.length > 0 ? (
                        comparisonResult.added_content.map((item, idx) => (
                          <li key={idx} className="text-green-600 flex items-start gap-2">
                            <span className="text-green-500">•</span>
                            <span>{item}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-gray-500 italic">لا توجد إضافات جديدة</li>
                      )}
                    </ul>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border">
                    <h4 className="font-semibold text-blue-700 mb-2 flex items-center gap-2">
                      <span className="text-2xl">{comparisonResult.questions_changes.length}</span>
                      ❓ أسئلة محدثة
                    </h4>
                    <ul className="text-sm space-y-1 max-h-32 overflow-y-auto">
                      {comparisonResult.questions_changes.length > 0 ? (
                        comparisonResult.questions_changes.map((item, idx) => (
                          <li key={idx} className="text-blue-600 flex items-start gap-2">
                            <span className="text-blue-500">•</span>
                            <span>{item}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-gray-500 italic">لا توجد تحديثات في الأسئلة</li>
                      )}
                    </ul>
                  </div>
                </div>
                
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-red-700 mb-2 flex items-center gap-2">
                    <span className="text-2xl">{comparisonResult.major_differences.length}</span>
                    🚨 تغييرات رئيسية تحتاج انتباه
                  </h4>
                  <ul className="text-sm space-y-1 max-h-32 overflow-y-auto">
                    {comparisonResult.major_differences.length > 0 ? (
                      comparisonResult.major_differences.map((item, idx) => (
                        <li key={idx} className="text-red-600 flex items-start gap-2">
                          <span className="text-red-500">⚠</span>
                          <span className="font-medium">{item}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-gray-500 italic">لا توجد تغييرات رئيسية</li>
                    )}
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Processing Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Eye className="w-5 h-5" />
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
                  <BarChart3 className="w-5 h-5" />
                  ثقة التحليل
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-600">
                  {comparisonResult ? `${Math.round(comparisonResult.confidence_score * 100)}%` : '--'}
                </div>
                <p className="text-sm text-gray-600 mt-1">🎯 دقة Gemini AI</p>
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
                <div className="text-3xl font-bold text-blue-600">
                  {totalProcessingTime > 0 ? `${totalProcessingTime.toFixed(1)}s` : '--'}
                </div>
                <p className="text-sm text-gray-600 mt-1">إجمالي الوقت</p>
              </CardContent>
            </Card>
          </div>

          {/* Visual Analysis Section */}
          <Card className="border-2 border-gray-200 bg-gray-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-800">
                <Eye className="w-6 h-6" />
                👁️ التحليل البصري
              </CardTitle>
              <CardDescription className="text-gray-700">
                تحليل الصور والعناصر البصرية
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-gray-800 mb-2">📸 الصورة القديمة</h4>
                  {oldImageResult ? (
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">دقة الاستخراج:</span>
                        <Badge variant="outline">{Math.round(oldImageResult.confidence * 100)}%</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">عدد الكلمات:</span>
                        <span className="text-sm font-mono">{oldImageResult.word_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">الأبعاد:</span>
                        <span className="text-sm font-mono">
                          {oldImageResult.image_info?.width} × {oldImageResult.image_info?.height}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">لا توجد بيانات متاحة</p>
                  )}
                </div>
                
                <div className="bg-white p-4 rounded-lg border">
                  <h4 className="font-semibold text-gray-800 mb-2">📸 الصورة الجديدة</h4>
                  {newImageResult ? (
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">دقة الاستخراج:</span>
                        <Badge variant="outline">{Math.round(newImageResult.confidence * 100)}%</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">عدد الكلمات:</span>
                        <span className="text-sm font-mono">{newImageResult.word_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">الأبعاد:</span>
                        <span className="text-sm font-mono">
                          {newImageResult.image_info?.width} × {newImageResult.image_info?.height}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">لا توجد بيانات متاحة</p>
                  )}
                </div>
              </div>
              
              <div className="bg-white p-4 rounded-lg border">
                <h4 className="font-semibold text-gray-800 mb-2">📊 مقارنة بصرية</h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-lg font-bold text-blue-600">
                      {oldImageResult && newImageResult 
                        ? Math.abs(oldImageResult.word_count - newImageResult.word_count)
                        : 0
                      }
                    </div>
                    <div className="text-xs text-gray-600">فرق عدد الكلمات</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-purple-600">
                      {oldImageResult && newImageResult 
                        ? Math.abs(oldImageResult.character_count - newImageResult.character_count)
                        : 0
                      }
                    </div>
                    <div className="text-xs text-gray-600">فرق عدد الأحرف</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-green-600">
                      {oldImageResult && newImageResult 
                        ? Math.round(((oldImageResult.confidence + newImageResult.confidence) / 2) * 100)
                        : 0
                      }%
                    </div>
                    <div className="text-xs text-gray-600">متوسط الدقة</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
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