
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  Download, 
  FileText, 
  Image, 
  BarChart3, 
  Eye, 
  EyeOff,
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Clock,
  Users
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useRealComparison } from '@/hooks/useRealComparison';

interface ComparisonDashboardProps {
  files: { old: File[], new: File[] };
}

const ComparisonDashboard: React.FC<ComparisonDashboardProps> = ({ files }) => {
  const [selectedComparison, setSelectedComparison] = useState(null);
  const [showDifferences, setShowDifferences] = useState(true);
  const { toast } = useToast();
  
  const {
    isProcessing,
    progress,
    currentFile,
    currentFileType,
    oldResults,
    newResults,
    comparisons,
    error,
    startComparison,
    exportHTMLReport,
    exportMarkdownReport,
    resetState
  } = useRealComparison();

  useEffect(() => {
    console.log('🚀 ComparisonDashboard: بدء تشغيل لوحة المقارنة');
    console.log('📁 الملفات المرفوعة:', { 
      oldFiles: files.old.length, 
      newFiles: files.new.length 
    });

    if (files.old.length > 0 && files.new.length > 0) {
      console.log('🔄 بدء عملية المقارنة التلقائية');
      const sessionName = `مقارنة_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`;
      startComparison(files.old, files.new, sessionName);
    }
  }, [files, startComparison]);

  useEffect(() => {
    if (comparisons.length > 0 && !selectedComparison) {
      console.log('📋 تحديد أول مقارنة كمقارنة مختارة');
      setSelectedComparison(comparisons[0]);
    }
  }, [comparisons, selectedComparison]);

  const getStatusColor = (similarity: number) => {
    if (similarity >= 95) return 'bg-green-500';
    if (similarity >= 80) return 'bg-yellow-500';
    if (similarity >= 60) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getStatusText = (similarity: number) => {
    if (similarity >= 95) return 'متطابق تقريباً';
    if (similarity >= 80) return 'تغييرات طفيفة';
    if (similarity >= 60) return 'تغييرات متوسطة';
    return 'اختلافات كبيرة';
  };

  const handleExportHTML = async () => {
    console.log('📤 بدء تصدير تقرير HTML');
    try {
      await exportHTMLReport();
      console.log('✅ تم تصدير تقرير HTML بنجاح');
    } catch (error) {
      console.error('❌ فشل في تصدير HTML:', error);
    }
  };

  const handleExportMarkdown = async () => {
    console.log('📤 بدء تصدير تقرير Markdown');
    try {
      await exportMarkdownReport();
      console.log('✅ تم تصدير تقرير Markdown بنجاح');
    } catch (error) {
      console.error('❌ فشل في تصدير Markdown:', error);
    }
  };

  if (error) {
    console.error('💥 خطأ في عملية المقارنة:', error);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <div className="text-red-500 mb-4">
            <AlertTriangle className="w-16 h-16 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">حدث خطأ</h2>
            <p className="text-lg">{error}</p>
          </div>
          <Button onClick={resetState}>إعادة المحاولة</Button>
        </div>
      </section>
    );
  }

  if (isProcessing) {
    console.log(`⏳ معلالجة: ${progress}% - ${currentFileType}: ${currentFile}`);
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">جاري معالجة الملفات...</h2>
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

            {currentFile && (
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-blue-600 font-medium">{currentFileType}</div>
                <div className="text-lg font-bold text-blue-800">{currentFile}</div>
              </div>
            )}

            <div className="grid md:grid-cols-3 gap-4">
              <Card className="p-4 text-center">
                <FileText className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                <div className="text-sm text-gray-600">استخراج النصوص</div>
                <div className="text-lg font-bold text-blue-600">
                  {progress < 70 ? 'جاري...' : 'مكتمل'}
                </div>
              </Card>
              <Card className="p-4 text-center">
                <Image className="w-8 h-8 mx-auto mb-2 text-green-500" />
                <div className="text-sm text-gray-600">المقارنة البصرية</div>
                <div className="text-lg font-bold text-green-600">
                  {progress < 75 ? 'انتظار...' : 'جاري...'}
                </div>
              </Card>
              <Card className="p-4 text-center">
                <BarChart3 className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                <div className="text-sm text-gray-600">تحليل البيانات</div>
                <div className="text-lg font-bold text-purple-600">
                  {progress < 90 ? 'انتظار...' : 'جاري...'}
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (comparisons.length === 0) {
    console.log('📭 لا توجد نتائج مقارنة');
    return (
      <section className="container mx-auto px-6 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold mb-2">لا توجد نتائج</h2>
          <p className="text-lg text-gray-600">لم يتم العثور على نتائج مقارنة</p>
        </div>
      </section>
    );
  }

  console.log('📊 عرض نتائج المقارنة:', {
    comparisons: comparisons.length,
    oldResults: oldResults.length,
    newResults: newResults.length
  });

  const overallStats = {
    totalFiles: comparisons.length,
    avgSimilarity: comparisons.reduce((acc, r) => acc + r.similarity, 0) / comparisons.length,
    highSimilarity: comparisons.filter(r => r.similarity >= 80).length,
    lowSimilarity: comparisons.filter(r => r.similarity < 60).length
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      {/* شريط علوي */}
      <header className="bg-white shadow-sm border-b p-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={resetState}>
              <ArrowLeft className="w-4 h-4 ml-2" />
              العودة للرفع
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">نتائج المقارنة</h1>
              <p className="text-sm text-gray-600">
                تم مقارنة {comparisons.length} ملف باستخدام الذكاء الاصطناعي
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleExportHTML} variant="outline" size="sm">
              <Download className="w-4 h-4 ml-2" />
              تصدير HTML
            </Button>
            <Button onClick={handleExportMarkdown} size="sm">
              <Download className="w-4 h-4 ml-2" />
              تصدير Markdown
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* إحصائيات سريعة */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{overallStats.totalFiles}</div>
            <div className="text-sm text-gray-600">إجمالي الملفات</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{overallStats.highSimilarity}</div>
            <div className="text-sm text-gray-600">عالية التطابق</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">{overallStats.lowSimilarity}</div>
            <div className="text-sm text-gray-600">منخفضة التطابق</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{Math.round(overallStats.avgSimilarity)}%</div>
            <div className="text-sm text-gray-600">متوسط التطابق</div>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* قائمة النتائج */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  قائمة المقارنات
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="max-h-96 overflow-y-auto">
                  {comparisons.map((result, index) => (
                    <div
                      key={result.id}
                      className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedComparison?.id === result.id ? 'bg-blue-50 border-r-4 border-r-blue-500' : ''
                      }`}
                      onClick={() => {
                        console.log('🔍 اختيار مقارنة:', result.id);
                        setSelectedComparison(result);
                      }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm font-medium truncate">{result.newFileName}</div>
                        <Badge className={`${getStatusColor(result.similarity)} text-white text-xs`}>
                          {getStatusText(result.similarity)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-600">
                        <span>التطابق: {result.similarity}%</span>
                      </div>
                      <div className="mt-2">
                        <Progress value={result.similarity} className="h-1" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* تفاصيل المقارنة */}
          <div className="lg:col-span-2">
            {selectedComparison ? (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">
                      تفاصيل المقارنة: {selectedComparison.newFileName}
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowDifferences(!showDifferences)}
                    >
                      {showDifferences ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      {showDifferences ? 'إخفاء' : 'إظهار'} التفاصيل
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="comparison" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="comparison">المقارنة</TabsTrigger>
                      <TabsTrigger value="changes">التغييرات</TabsTrigger>
                      <TabsTrigger value="text">النصوص المستخرجة</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="comparison" className="space-y-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium mb-2">الملف القديم</h4>
                          <div className="bg-gray-100 rounded-lg p-4 min-h-32">
                            <div className="text-sm text-gray-600">
                              <strong>اسم الملف:</strong> {selectedComparison.oldFileName}
                            </div>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2">الملف الجديد</h4>
                          <div className="bg-gray-100 rounded-lg p-4 min-h-32">
                            <div className="text-sm text-gray-600">
                              <strong>اسم الملف:</strong> {selectedComparison.newFileName}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-center p-6 bg-blue-50 rounded-lg">
                        <div className="text-3xl font-bold text-blue-600 mb-2">
                          {selectedComparison.similarity}%
                        </div>
                        <div className="text-sm text-gray-600">نسبة التطابق الإجمالية</div>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="changes" className="space-y-4">
                      <div>
                        <h4 className="font-medium mb-3">التغييرات المكتشفة:</h4>
                        <div className="space-y-3">
                          {selectedComparison.analysis.content_changes?.length > 0 && (
                            <div>
                              <h5 className="font-medium text-sm mb-2">تغييرات المحتوى:</h5>
                              <div className="space-y-1">
                                {selectedComparison.analysis.content_changes.map((change, index) => (
                                  <div key={index} className="flex items-center gap-3 p-2 bg-orange-50 rounded text-sm">
                                    <AlertTriangle className="w-4 h-4 text-orange-500 flex-shrink-0" />
                                    <span>{change}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {selectedComparison.analysis.questions_changes?.length > 0 && (
                            <div>
                              <h5 className="font-medium text-sm mb-2">تغييرات الأسئلة:</h5>
                              <div className="space-y-1">
                                {selectedComparison.analysis.questions_changes.map((change, index) => (
                                  <div key={index} className="flex items-center gap-3 p-2 bg-blue-50 rounded text-sm">
                                    <CheckCircle className="w-4 h-4 text-blue-500 flex-shrink-0" />
                                    <span>{change}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {selectedComparison.analysis.summary && (
                            <div className="p-4 bg-gray-50 rounded-lg">
                              <h5 className="font-medium mb-2">ملخص التحليل:</h5>
                              <p className="text-sm text-gray-700">{selectedComparison.analysis.summary}</p>
                            </div>
                          )}

                          {selectedComparison.analysis.recommendation && (
                            <div className="p-4 bg-green-50 rounded-lg">
                              <h5 className="font-medium mb-2">التوصيات:</h5>
                              <p className="text-sm text-green-700">{selectedComparison.analysis.recommendation}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="text" className="space-y-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium mb-2">النص المستخرج من الملف القديم:</h4>
                          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                            <pre className="text-xs whitespace-pre-wrap">
                              {oldResults.find(r => r.fileName === selectedComparison.oldFileName)?.extractedText || 'لا يوجد نص مستخرج'}
                            </pre>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2">النص المستخرج من الملف الجديد:</h4>
                          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                            <pre className="text-xs whitespace-pre-wrap">
                              {newResults.find(r => r.fileName === selectedComparison.newFileName)?.extractedText || 'لا يوجد نص مستخرج'}
                            </pre>
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <Card className="p-8 text-center">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">اختر مقارنة من القائمة لعرض التفاصيل</p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComparisonDashboard;
