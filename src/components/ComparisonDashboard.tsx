
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

interface ComparisonDashboardProps {
  files: { old: File[], new: File[] };
}

interface ComparisonResult {
  id: string;
  oldFileName: string;
  newFileName: string;
  visualSimilarity: number;
  textSimilarity: number;
  overallScore: number;
  changes: string[];
  status: 'identical' | 'minor-changes' | 'major-changes' | 'completely-different';
  processingTime: number;
}

const ComparisonDashboard: React.FC<ComparisonDashboardProps> = ({ files }) => {
  const [results, setResults] = useState<ComparisonResult[]>([]);
  const [selectedComparison, setSelectedComparison] = useState<ComparisonResult | null>(null);
  const [showDifferences, setShowDifferences] = useState(true);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(true);
  const { toast } = useToast();

  // محاكاة معالجة الملفات
  useEffect(() => {
    const simulateProcessing = async () => {
      const totalFiles = Math.max(files.old.length, files.new.length);
      const mockResults: ComparisonResult[] = [];

      for (let i = 0; i < totalFiles; i++) {
        // محاكاة التقدم
        setProcessingProgress(((i + 1) / totalFiles) * 100);
        
        // إنشاء نتائج وهمية
        const visualSim = Math.random() * 40 + 60; // 60-100%
        const textSim = Math.random() * 30 + 70;   // 70-100%
        const overall = (visualSim + textSim) / 2;
        
        let status: ComparisonResult['status'] = 'identical';
        if (overall < 70) status = 'completely-different';
        else if (overall < 80) status = 'major-changes';
        else if (overall < 95) status = 'minor-changes';

        mockResults.push({
          id: `comparison-${i}`,
          oldFileName: files.old[i]?.name || `صفحة قديمة ${i + 1}`,
          newFileName: files.new[i]?.name || `صفحة جديدة ${i + 1}`,
          visualSimilarity: Math.round(visualSim),
          textSimilarity: Math.round(textSim),
          overallScore: Math.round(overall),
          changes: [
            'تغيير في العنوان الرئيسي',
            'إضافة صورة جديدة',
            'تعديل في النص التوضيحي',
            'تحديث الأرقام والإحصائيات'
          ].slice(0, Math.floor(Math.random() * 4) + 1),
          status,
          processingTime: Math.random() * 5 + 2
        });

        await new Promise(resolve => setTimeout(resolve, 500));
      }

      setResults(mockResults);
      setIsProcessing(false);
      setSelectedComparison(mockResults[0]);
    };

    simulateProcessing();
  }, [files]);

  const getStatusColor = (status: ComparisonResult['status']) => {
    switch (status) {
      case 'identical': return 'bg-green-500';
      case 'minor-changes': return 'bg-yellow-500';
      case 'major-changes': return 'bg-orange-500';
      case 'completely-different': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = (status: ComparisonResult['status']) => {
    switch (status) {
      case 'identical': return 'متطابق';
      case 'minor-changes': return 'تغييرات طفيفة';
      case 'major-changes': return 'تغييرات كبيرة';
      case 'completely-different': return 'مختلف تماماً';
      default: return 'غير محدد';
    }
  };

  const exportReport = () => {
    toast({
      title: "جاري التصدير",
      description: "سيتم تحميل التقرير قريباً..."
    });
  };

  const exportPowerPoint = () => {
    toast({
      title: "جاري إنشاء العرض التقديمي",
      description: "سيتم تحميل ملف PowerPoint قريباً..."
    });
  };

  if (isProcessing) {
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
                <span>{Math.round(processingProgress)}%</span>
              </div>
              <Progress value={processingProgress} className="h-3" />
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <Card className="p-4 text-center">
                <FileText className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                <div className="text-sm text-gray-600">استخراج النصوص</div>
                <div className="text-lg font-bold text-blue-600">جاري...</div>
              </Card>
              <Card className="p-4 text-center">
                <Image className="w-8 h-8 mx-auto mb-2 text-green-500" />
                <div className="text-sm text-gray-600">المقارنة البصرية</div>
                <div className="text-lg font-bold text-green-600">جاري...</div>
              </Card>
              <Card className="p-4 text-center">
                <BarChart3 className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                <div className="text-sm text-gray-600">تحليل البيانات</div>
                <div className="text-lg font-bold text-purple-600">جاري...</div>
              </Card>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const overallStats = {
    totalFiles: results.length,
    identical: results.filter(r => r.status === 'identical').length,
    changed: results.filter(r => r.status !== 'identical').length,
    avgSimilarity: results.reduce((acc, r) => acc + r.overallScore, 0) / results.length,
    processingTime: results.reduce((acc, r) => acc + r.processingTime, 0)
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      {/* شريط علوي */}
      <header className="bg-white shadow-sm border-b p-4">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 ml-2" />
              العودة للرفع
            </Button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">نتائج المقارنة</h1>
              <p className="text-sm text-gray-600">
                تم مقارنة {results.length} ملف في {Math.round(overallStats.processingTime)} ثانية
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={exportReport} variant="outline" size="sm">
              <Download className="w-4 h-4 ml-2" />
              تصدير PDF
            </Button>
            <Button onClick={exportPowerPoint} size="sm">
              <Download className="w-4 h-4 ml-2" />
              تصدير PowerPoint
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
            <div className="text-2xl font-bold text-green-600">{overallStats.identical}</div>
            <div className="text-sm text-gray-600">متطابقة</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">{overallStats.changed}</div>
            <div className="text-sm text-gray-600">متغيرة</div>
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
                  {results.map((result) => (
                    <div
                      key={result.id}
                      className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedComparison?.id === result.id ? 'bg-blue-50 border-r-4 border-r-blue-500' : ''
                      }`}
                      onClick={() => setSelectedComparison(result)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm font-medium truncate">{result.newFileName}</div>
                        <Badge className={`${getStatusColor(result.status)} text-white text-xs`}>
                          {getStatusText(result.status)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-600">
                        <span>بصري: {result.visualSimilarity}%</span>
                        <span>نصي: {result.textSimilarity}%</span>
                      </div>
                      <div className="mt-2">
                        <Progress value={result.overallScore} className="h-1" />
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
                      {showDifferences ? 'إخفاء' : 'إظهار'} الاختلافات
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="comparison" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="comparison">المقارنة</TabsTrigger>
                      <TabsTrigger value="changes">التغييرات</TabsTrigger>
                      <TabsTrigger value="stats">الإحصائيات</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="comparison" className="space-y-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium mb-2">المنهج القديم</h4>
                          <div className="bg-gray-100 rounded-lg p-4 min-h-64 flex items-center justify-center">
                            <div className="text-center text-gray-500">
                              <FileText className="w-12 h-12 mx-auto mb-2" />
                              <p>{selectedComparison.oldFileName}</p>
                            </div>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2">المنهج الجديد</h4>
                          <div className="bg-gray-100 rounded-lg p-4 min-h-64 flex items-center justify-center">
                            <div className="text-center text-gray-500">
                              <FileText className="w-12 h-12 mx-auto mb-2" />
                              <p>{selectedComparison.newFileName}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4 mt-4">
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {selectedComparison.visualSimilarity}%
                          </div>
                          <div className="text-sm text-gray-600">تطابق بصري</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {selectedComparison.textSimilarity}%
                          </div>
                          <div className="text-sm text-gray-600">تطابق نصي</div>
                        </div>
                        <div className="text-center p-4 bg-purple-50 rounded-lg">
                          <div className="text-2xl font-bold text-purple-600">
                            {selectedComparison.overallScore}%
                          </div>
                          <div className="text-sm text-gray-600">التطابق الإجمالي</div>
                        </div>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="changes" className="space-y-4">
                      <div>
                        <h4 className="font-medium mb-3">التغييرات المكتشفة:</h4>
                        <div className="space-y-2">
                          {selectedComparison.changes.map((change, index) => (
                            <div key={index} className="flex items-center gap-3 p-3 bg-orange-50 rounded-lg">
                              <AlertTriangle className="w-4 h-4 text-orange-500 flex-shrink-0" />
                              <span className="text-sm">{change}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="stats" className="space-y-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">وقت المعالجة</span>
                            <span className="font-medium">{selectedComparison.processingTime.toFixed(1)}ث</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">حالة التطابق</span>
                            <Badge className={`${getStatusColor(selectedComparison.status)} text-white`}>
                              {getStatusText(selectedComparison.status)}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">عدد التغييرات</span>
                            <span className="font-medium">{selectedComparison.changes.length}</span>
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
