
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
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
  Zap
} from 'lucide-react';
import { ProcessingResult, ComparisonResult } from '@/services/realAIServices';

interface AdvancedComparisonDashboardProps {
  isProcessing: boolean;
  progress: number;
  currentFile: string;
  currentFileType: string;
  oldResults: ProcessingResult[];
  newResults: ProcessingResult[];
  comparisons: ComparisonResult[];
  onExportHTML: () => void;
  onExportMarkdown: () => void;
  onBack: () => void;
}

const AdvancedComparisonDashboard: React.FC<AdvancedComparisonDashboardProps> = ({
  isProcessing,
  progress,
  currentFile,
  currentFileType,
  oldResults,
  newResults,
  comparisons,
  onExportHTML,
  onExportMarkdown,
  onBack
}) => {
  const [selectedComparison, setSelectedComparison] = useState<ComparisonResult | null>(null);
  const [selectedOldResult, setSelectedOldResult] = useState<ProcessingResult | null>(null);
  const [selectedNewResult, setSelectedNewResult] = useState<ProcessingResult | null>(null);

  if (isProcessing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
        <div className="container mx-auto px-6 py-16">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                جاري المعالجة باستخدام الذكاء الاصطناعي...
              </h2>
              <p className="text-lg text-gray-600">
                {currentFileType}: {currentFile}
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

              <div className="grid md:grid-cols-3 gap-4">
                <Card className="p-4 text-center">
                  <Zap className="w-8 h-8 mx-auto mb-2 text-orange-500" />
                  <div className="text-sm text-gray-600">Landing.AI OCR</div>
                  <div className="text-lg font-bold text-orange-600">جاري...</div>
                </Card>
                <Card className="p-4 text-center">
                  <Image className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <div className="text-sm text-gray-600">معالجة الصور</div>
                  <div className="text-lg font-bold text-green-600">جاري...</div>
                </Card>
                <Card className="p-4 text-center">
                  <BarChart3 className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                  <div className="text-sm text-gray-600">مقارنة Gemini</div>
                  <div className="text-lg font-bold text-purple-600">انتظار...</div>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const totalFiles = Math.max(oldResults.length, newResults.length);
  const completedComparisons = comparisons.filter(c => c.status === 'completed').length;
  const avgSimilarity = comparisons.reduce((acc, c) => acc + c.similarity, 0) / comparisons.length || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      {/* شريط علوي */}
      <header className="bg-white shadow-sm border-b p-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 ml-2" />
              العودة للرفع
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">نتائج المقارنة المتقدمة</h1>
              <p className="text-sm text-gray-600">
                تم مقارنة {completedComparisons} من {totalFiles} ملف باستخدام الذكاء الاصطناعي
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={onExportHTML} variant="outline" size="sm">
              <Download className="w-4 h-4 ml-2" />
              تصدير HTML
            </Button>
            <Button onClick={onExportMarkdown} size="sm">
              <Download className="w-4 h-4 ml-2" />
              تصدير MD الشامل
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* إحصائيات سريعة */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{totalFiles}</div>
            <div className="text-sm text-gray-600">إجمالي الملفات</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{completedComparisons}</div>
            <div className="text-sm text-gray-600">مقارنات مكتملة</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{Math.round(avgSimilarity)}%</div>
            <div className="text-sm text-gray-600">متوسط التطابق</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">AI</div>
            <div className="text-sm text-gray-600">مدعوم بالذكاء الاصطناعي</div>
          </Card>
        </div>

        {/* الواجهة المقسومة */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* القسم الأيسر: الكتاب القديم */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-orange-600">
                <FileText className="w-5 h-5" />
                الكتاب القديم ({oldResults.length} صفحة)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                {oldResults.map((result, index) => (
                  <div
                    key={result.id}
                    className={`p-3 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedOldResult?.id === result.id ? 'bg-orange-50 border-r-4 border-r-orange-500' : ''
                    }`}
                    onClick={() => setSelectedOldResult(result)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-medium truncate">{result.fileName}</div>
                      <Badge className={`${
                        result.status === 'completed' ? 'bg-green-500' : 
                        result.status === 'error' ? 'bg-red-500' : 'bg-gray-500'
                      } text-white text-xs`}>
                        {result.status === 'completed' ? 'مكتمل' : 
                         result.status === 'error' ? 'خطأ' : 'معالجة'}
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-600">
                      ثقة: {Math.round(result.confidence * 100)}%
                    </div>
                  </div>
                ))}
              </ScrollArea>
            </CardContent>
          </Card>

          {/* القسم الأيمن: الكتاب الجديد */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-600">
                <FileText className="w-5 h-5" />
                الكتاب الجديد ({newResults.length} صفحة)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                {newResults.map((result, index) => (
                  <div
                    key={result.id}
                    className={`p-3 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedNewResult?.id === result.id ? 'bg-blue-50 border-r-4 border-r-blue-500' : ''
                    }`}
                    onClick={() => setSelectedNewResult(result)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-medium truncate">{result.fileName}</div>
                      <Badge className={`${
                        result.status === 'completed' ? 'bg-green-500' : 
                        result.status === 'error' ? 'bg-red-500' : 'bg-gray-500'
                      } text-white text-xs`}>
                        {result.status === 'completed' ? 'مكتمل' : 
                         result.status === 'error' ? 'خطأ' : 'معالجة'}
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-600">
                      ثقة: {Math.round(result.confidence * 100)}%
                    </div>
                  </div>
                ))}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* قسم المقارنات والتحليل */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              نتائج المقارنة بالذكاء الاصطناعي
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              {/* قائمة المقارنات */}
              <div className="md:col-span-1">
                <h4 className="font-medium mb-3">قائمة المقارنات</h4>
                <ScrollArea className="h-64">
                  {comparisons.map((comparison, index) => (
                    <div
                      key={comparison.id}
                      className={`p-3 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedComparison?.id === comparison.id ? 'bg-purple-50 border-r-4 border-r-purple-500' : ''
                      }`}
                      onClick={() => setSelectedComparison(comparison)}
                    >
                      <div className="text-sm font-medium mb-1">مقارنة {index + 1}</div>
                      <div className="text-xs text-gray-600 mb-2">
                        {comparison.oldFileName} ↔ {comparison.newFileName}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs">تطابق: {comparison.similarity}%</span>
                        <Badge className={`${
                          comparison.similarity > 90 ? 'bg-green-500' :
                          comparison.similarity > 70 ? 'bg-yellow-500' : 'bg-red-500'
                        } text-white text-xs`}>
                          {comparison.similarity > 90 ? 'عالي' :
                           comparison.similarity > 70 ? 'متوسط' : 'منخفض'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              </div>

              {/* تفاصيل المقارنة المختارة */}
              <div className="md:col-span-2">
                {selectedComparison ? (
                  <Tabs defaultValue="analysis" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="analysis">التحليل</TabsTrigger>
                      <TabsTrigger value="changes">التغييرات</TabsTrigger>
                      <TabsTrigger value="recommendations">التوصيات</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="analysis" className="space-y-4">
                      <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <div className="text-3xl font-bold text-purple-600 mb-2">
                          {selectedComparison.similarity}%
                        </div>
                        <div className="text-sm text-gray-600">نسبة التطابق الإجمالية</div>
                      </div>
                      <div>
                        <h5 className="font-medium mb-2">ملخص التحليل:</h5>
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {selectedComparison.analysis.summary}
                        </p>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="changes" className="space-y-4">
                      <div>
                        <h5 className="font-medium mb-2">تغييرات المحتوى:</h5>
                        <ul className="space-y-1">
                          {selectedComparison.analysis.content_changes?.map((change, idx) => (
                            <li key={idx} className="text-sm flex items-start gap-2">
                              <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                              {change}
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h5 className="font-medium mb-2">تغييرات الأسئلة:</h5>
                        <ul className="space-y-1">
                          {selectedComparison.analysis.questions_changes?.map((change, idx) => (
                            <li key={idx} className="text-sm flex items-start gap-2">
                              <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                              {change}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="recommendations" className="space-y-4">
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <h5 className="font-medium mb-2 text-blue-800">توصيات للمعلم:</h5>
                        <p className="text-sm text-blue-700">
                          {selectedComparison.analysis.recommendation}
                        </p>
                      </div>
                      
                      <div>
                        <h5 className="font-medium mb-2">الاختلافات الرئيسية:</h5>
                        <ul className="space-y-1">
                          {selectedComparison.analysis.major_differences?.map((diff, idx) => (
                            <li key={idx} className="text-sm flex items-start gap-2">
                              <Eye className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                              {diff}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </TabsContent>
                  </Tabs>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p>اختر مقارنة من القائمة لعرض التفاصيل</p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdvancedComparisonDashboard;
