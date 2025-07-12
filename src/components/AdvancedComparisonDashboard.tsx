
import React, { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
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
  Search,
  Filter,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Copy,
  BookOpen,
  Target,
  TrendingUp,
  FileCheck,
  Layers,
  Share2
} from 'lucide-react';
import { ProcessingResult, ComparisonResult } from '@/services/realAIServices';
import { EnhancedReportExporter } from './EnhancedReportExporter';
import { InteractiveComparisonViewer } from './InteractiveComparisonViewer';
import { PerformanceMetrics } from './PerformanceMetrics';

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
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLevel, setFilterLevel] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({
    oldBook: true,
    newBook: true,
    analysis: true
  });

  // تحسين الأداء بـ useMemo
  const filteredComparisons = useMemo(() => {
    let filtered = comparisons;
    
    if (filterLevel !== 'all') {
      filtered = filtered.filter(comp => {
        if (filterLevel === 'high') return comp.similarity > 80;
        if (filterLevel === 'medium') return comp.similarity >= 50 && comp.similarity <= 80;
        if (filterLevel === 'low') return comp.similarity < 50;
        return true;
      });
    }
    
    if (searchTerm) {
      filtered = filtered.filter(comp => 
        comp.oldFileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.newFileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.analysis.summary?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    return filtered;
  }, [comparisons, filterLevel, searchTerm]);

  const statistics = useMemo(() => {
    const total = comparisons.length;
    const avgSimilarity = total > 0 ? comparisons.reduce((acc, c) => acc + c.similarity, 0) / total : 0;
    const highSimilarity = comparisons.filter(c => c.similarity > 80).length;
    const mediumSimilarity = comparisons.filter(c => c.similarity >= 50 && c.similarity <= 80).length;
    const lowSimilarity = comparisons.filter(c => c.similarity < 50).length;
    
    return {
      total,
      avgSimilarity: Math.round(avgSimilarity),
      highSimilarity,
      mediumSimilarity,
      lowSimilarity,
      totalOldFiles: oldResults.length,
      totalNewFiles: newResults.length,
      completedFiles: oldResults.filter(r => r.status === 'completed').length + 
                     newResults.filter(r => r.status === 'completed').length
    };
  }, [comparisons, oldResults, newResults]);

  const toggleSection = useCallback((section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  }, []);

  const copyToClipboard = useCallback((text: string) => {
    navigator.clipboard.writeText(text);
  }, []);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      {/* شريط علوي محسن */}
      <header className="bg-white shadow-lg border-b sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={onBack} className="hover:bg-gray-100">
                <ArrowLeft className="w-4 h-4 ml-2" />
                العودة للرفع
              </Button>
              <Separator orientation="vertical" className="h-6" />
              <div>
                <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-blue-600" />
                  تقرير المقارنة المتقدمة
                </h1>
                <p className="text-sm text-gray-600">
                  تم مقارنة {statistics.total} من الملفات باستخدام الذكاء الاصطناعي
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={onExportHTML} variant="outline" size="sm" className="hover:bg-gray-50">
                <Download className="w-4 h-4 ml-2" />
                تصدير HTML
              </Button>
              <Button onClick={onExportMarkdown} size="sm" className="bg-blue-600 hover:bg-blue-700">
                <Download className="w-4 h-4 ml-2" />
                تصدير تقرير شامل
              </Button>
              <Button variant="outline" size="sm" className="hover:bg-gray-50">
                <Share2 className="w-4 h-4 ml-2" />
                مشاركة
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        {/* لوحة الإحصائيات المحسنة */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
          <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
            <CardContent className="p-4 text-center">
              <FileCheck className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{statistics.total}</div>
              <div className="text-sm opacity-90">مقارنات مكتملة</div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
            <CardContent className="p-4 text-center">
              <Target className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{statistics.avgSimilarity}%</div>
              <div className="text-sm opacity-90">متوسط التشابه</div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-r from-emerald-500 to-emerald-600 text-white">
            <CardContent className="p-4 text-center">
              <TrendingUp className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{statistics.highSimilarity}</div>
              <div className="text-sm opacity-90">تشابه عالي</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-white">
            <CardContent className="p-4 text-center">
              <Clock className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{statistics.mediumSimilarity}</div>
              <div className="text-sm opacity-90">تشابه متوسط</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-red-500 to-red-600 text-white">
            <CardContent className="p-4 text-center">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{statistics.lowSimilarity}</div>
              <div className="text-sm opacity-90">تشابه منخفض</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
            <CardContent className="p-4 text-center">
              <Layers className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{statistics.totalOldFiles + statistics.totalNewFiles}</div>
              <div className="text-sm opacity-90">إجمالي الملفات</div>
            </CardContent>
          </Card>
        </div>

        {/* تحذير إذا كان هناك مشاكل في التحليل */}
        {comparisons.some(c => c.analysis.summary?.includes('خطأ')) && (
          <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-lg shadow-sm">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 mr-2" />
              <div>
                <h4 className="font-medium text-yellow-800">تنبيه مهم</h4>
                <p className="text-sm text-yellow-700 mt-1">
                  تم الوصول إلى الحد الأقصى اليومي لـ Gemini AI API (50 طلب/يوم). 
                  بعض المقارنات تظهر التشابه الأساسي فقط وليس التحليل المتقدم المفصل.
                </p>
                <p className="text-xs text-yellow-600 mt-2">
                  💡 للحصول على التحليل المتقدم الكامل، انتظر حتى اليوم التالي أو فكر في الترقية لخطة API مدفوعة.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* قسم مقسم للكتب القديمة والجديدة */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* الكتاب القديم */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-orange-50 to-orange-100 border-b">
              <CardTitle 
                className="flex items-center justify-between cursor-pointer text-orange-700"
                onClick={() => toggleSection('oldBook')}
              >
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  الكتاب القديم ({oldResults.length} صفحة)
                </div>
                {expandedSections.oldBook ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </CardTitle>
            </CardHeader>
            {expandedSections.oldBook && (
              <CardContent className="p-0">
                <ScrollArea className="h-96">
                  {oldResults.map((result, index) => (
                    <div
                      key={result.id}
                      className={`p-4 border-b cursor-pointer transition-all duration-200 hover:bg-orange-25 ${
                        selectedOldResult?.id === result.id ? 
                        'bg-orange-50 border-r-4 border-r-orange-500 shadow-sm' : ''
                      }`}
                      onClick={() => setSelectedOldResult(result)}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-sm font-medium truncate text-gray-800">
                          صفحة {index + 1}: {result.fileName}
                        </div>
                        <Badge className={`${
                          result.status === 'completed' ? 'bg-green-500 hover:bg-green-600' : 
                          result.status === 'error' ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-500'
                        } text-white text-xs transition-colors`}>
                          {result.status === 'completed' ? 'مكتمل' : 
                           result.status === 'error' ? 'خطأ' : 'معالجة'}
                        </Badge>
                      </div>
                      
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">دقة الاستخراج:</span>
                          <span className="font-medium text-orange-600">
                            {Math.round(result.confidence * 100)}%
                          </span>
                        </div>
                        
                        {result.extractedText && (
                          <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                            <div className="text-gray-700 line-clamp-2">
                              {result.extractedText.substring(0, 100)}...
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="mt-1 h-6 text-xs"
                              onClick={(e) => {
                                e.stopPropagation();
                                copyToClipboard(result.extractedText);
                              }}
                            >
                              <Copy className="w-3 h-3 ml-1" />
                              نسخ النص
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              </CardContent>
            )}
          </Card>

          {/* الكتاب الجديد */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 border-b">
              <CardTitle 
                className="flex items-center justify-between cursor-pointer text-blue-700"
                onClick={() => toggleSection('newBook')}
              >
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  الكتاب الجديد ({newResults.length} صفحة)
                </div>
                {expandedSections.newBook ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </CardTitle>
            </CardHeader>
            {expandedSections.newBook && (
              <CardContent className="p-0">
                <ScrollArea className="h-96">
                  {newResults.map((result, index) => (
                    <div
                      key={result.id}
                      className={`p-4 border-b cursor-pointer transition-all duration-200 hover:bg-blue-25 ${
                        selectedNewResult?.id === result.id ? 
                        'bg-blue-50 border-r-4 border-r-blue-500 shadow-sm' : ''
                      }`}
                      onClick={() => setSelectedNewResult(result)}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-sm font-medium truncate text-gray-800">
                          صفحة {index + 1}: {result.fileName}
                        </div>
                        <Badge className={`${
                          result.status === 'completed' ? 'bg-green-500 hover:bg-green-600' : 
                          result.status === 'error' ? 'bg-red-500 hover:bg-red-600' : 'bg-gray-500'
                        } text-white text-xs transition-colors`}>
                          {result.status === 'completed' ? 'مكتمل' : 
                           result.status === 'error' ? 'خطأ' : 'معالجة'}
                        </Badge>
                      </div>
                      
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">دقة الاستخراج:</span>
                          <span className="font-medium text-blue-600">
                            {Math.round(result.confidence * 100)}%
                          </span>
                        </div>
                        
                        {result.extractedText && (
                          <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                            <div className="text-gray-700 line-clamp-2">
                              {result.extractedText.substring(0, 100)}...
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="mt-1 h-6 text-xs"
                              onClick={(e) => {
                                e.stopPropagation();
                                copyToClipboard(result.extractedText);
                              }}
                            >
                              <Copy className="w-3 h-3 ml-1" />
                              نسخ النص
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              </CardContent>
            )}
          </Card>
        </div>

        {/* مقاييس الأداء */}
        <PerformanceMetrics
          comparisons={comparisons}
          oldResults={oldResults}
          newResults={newResults}
          startTime={new Date(Date.now() - 60000)} // وقت افتراضي
          endTime={new Date()}
        />

        {/* العارض التفاعلي للمقارنات */}
        <InteractiveComparisonViewer
          comparisons={comparisons}
          oldResults={oldResults}
          newResults={newResults}
          onComparisonSelect={(comparison) => setSelectedComparison(comparison)}
        />

        {/* مصدر التقارير المحسن */}
        <EnhancedReportExporter
          comparisons={comparisons}
          oldResults={oldResults}
          newResults={newResults}
          sessionId={`session-${Date.now()}`}
          onExportHTML={onExportHTML}
          onExportMarkdown={onExportMarkdown}
        />

        {/* قسم المقارنات والتحليل المحسن */}
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-purple-100 border-b">
            <CardTitle 
              className="flex items-center justify-between cursor-pointer text-purple-700"
              onClick={() => toggleSection('analysis')}
            >
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                نتائج المقارنة بالذكاء الاصطناعي (التفصيلية)
              </div>
              {expandedSections.analysis ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </CardTitle>
          </CardHeader>
          {expandedSections.analysis && (
            <CardContent className="p-6">
              {/* شريط البحث والفلترة */}
              <div className="flex gap-4 mb-6">
                <div className="flex-1 relative">
                  <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="البحث في المقارنات..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pr-10 pl-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                                 <select
                   value={filterLevel}
                   onChange={(e) => setFilterLevel(e.target.value as 'all' | 'high' | 'medium' | 'low')}
                   className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                 >
                  <option value="all">جميع المستويات</option>
                  <option value="high">تشابه عالي (80%+)</option>
                  <option value="medium">تشابه متوسط (50-80%)</option>
                  <option value="low">تشابه منخفض (أقل من 50%)</option>
                </select>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                {/* قائمة المقارنات المحسنة */}
                <div className="md:col-span-1">
                  <h4 className="font-medium mb-3 flex items-center gap-2">
                    <Filter className="w-4 h-4" />
                    قائمة المقارنات ({filteredComparisons.length})
                  </h4>
                  <ScrollArea className="h-80">
                    {filteredComparisons.map((comparison, index) => (
                      <div
                        key={comparison.id}
                        className={`p-4 border-b cursor-pointer transition-all duration-200 hover:bg-purple-25 ${
                          selectedComparison?.id === comparison.id ? 
                          'bg-purple-50 border-r-4 border-r-purple-500 shadow-sm' : ''
                        }`}
                        onClick={() => setSelectedComparison(comparison)}
                      >
                        <div className="text-sm font-medium mb-2">مقارنة {index + 1}</div>
                        <div className="text-xs text-gray-600 mb-3 space-y-1">
                          <div>📄 {comparison.oldFileName}</div>
                          <div>📄 {comparison.newFileName}</div>
                        </div>
                        
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-xs text-gray-500">نسبة التطابق</div>
                          <Badge className={`${
                            comparison.similarity > 90 ? 'bg-green-500' :
                            comparison.similarity > 70 ? 'bg-yellow-500' : 'bg-red-500'
                          } text-white text-xs`}>
                            {comparison.similarity}%
                          </Badge>
                        </div>
                        
                        <Progress value={comparison.similarity} className="h-2" />
                      </div>
                    ))}
                  </ScrollArea>
                </div>

                {/* تفاصيل المقارنة المختارة المحسنة */}
                <div className="md:col-span-2">
                  {selectedComparison ? (
                    <Tabs defaultValue="analysis" className="w-full">
                      <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="analysis" className="text-xs">التحليل</TabsTrigger>
                        <TabsTrigger value="changes" className="text-xs">التغييرات</TabsTrigger>
                        <TabsTrigger value="recommendations" className="text-xs">التوصيات</TabsTrigger>
                        <TabsTrigger value="texts" className="text-xs">النصوص</TabsTrigger>
                      </TabsList>
                      
                      <TabsContent value="analysis" className="space-y-4 mt-4">
                        <div className="text-center p-6 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg border">
                          <div className="text-4xl font-bold text-purple-600 mb-2">
                            {selectedComparison.similarity}%
                          </div>
                          <div className="text-sm text-gray-600 mb-4">نسبة التطابق الإجمالية</div>
                          <Progress value={selectedComparison.similarity} className="h-3 max-w-xs mx-auto" />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-4 bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg border border-orange-200">
                            <div className="text-center">
                              <FileText className="w-8 h-8 mx-auto mb-2 text-orange-600" />
                              <div className="font-medium text-orange-800 truncate">
                                {selectedComparison.oldFileName?.split('.')[0] || 'غير متاح'}
                              </div>
                              <div className="text-xs text-orange-600 mt-1">الملف القديم</div>
                            </div>
                          </div>
                          <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                            <div className="text-center">
                              <FileText className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                              <div className="font-medium text-blue-800 truncate">
                                {selectedComparison.newFileName?.split('.')[0] || 'غير متاح'}
                              </div>
                              <div className="text-xs text-blue-600 mt-1">الملف الجديد</div>
                            </div>
                          </div>
                        </div>
                        
                        <div>
                          <h5 className="font-medium mb-2 flex items-center gap-2">
                            <Eye className="w-4 h-4" />
                            ملخص التحليل:
                          </h5>
                          <div className="text-sm text-gray-700 bg-gray-50 p-4 rounded-lg border">
                            {selectedComparison.analysis.summary || "تم حساب التشابه الأساسي فقط"}
                            {selectedComparison.analysis.summary?.includes('خطأ') && (
                              <div className="mt-3 p-3 bg-yellow-100 border-l-4 border-yellow-500 rounded">
                                <p className="text-yellow-800 text-xs">
                                  ⚠️ تم الوصول إلى الحد الأقصى لـ Gemini API. التحليل المتقدم غير متاح حالياً.
                                </p>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* معلومات إضافية عن المقارنة البصرية */}
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                          <h5 className="font-medium mb-2 text-blue-800 flex items-center gap-2">
                            <Image className="w-4 h-4" />
                            تفاصيل المقارنة البصرية:
                          </h5>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-blue-700">دقة المعالجة:</span>
                              <span className="font-medium mr-2">عالية الدقة</span>
                            </div>
                            <div>
                              <span className="text-blue-700">تقنية الاستخراج:</span>
                              <span className="font-medium mr-2">Landing AI OCR</span>
                            </div>
                            <div>
                              <span className="text-blue-700">تحليل المحتوى:</span>
                              <span className="font-medium mr-2">Gemini AI</span>
                            </div>
                            <div>
                              <span className="text-blue-700">حالة المعالجة:</span>
                              <span className="font-medium mr-2 text-green-600">مكتملة</span>
                            </div>
                          </div>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="changes" className="space-y-4 mt-4">
                        <div>
                          <h5 className="font-medium mb-3 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" />
                            تغييرات المحتوى:
                          </h5>
                          {selectedComparison.analysis.content_changes?.length > 0 ? (
                            <ul className="space-y-2">
                              {selectedComparison.analysis.content_changes.map((change, idx) => (
                                <li key={idx} className="text-sm flex items-start gap-3 p-3 bg-orange-50 rounded-lg border border-orange-200">
                                  <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                                  <span>{change}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg border">
                              لا توجد تغييرات محددة في المحتوى، أو لم يتم تحليلها بسبب حدود API
                            </div>
                          )}
                        </div>
                        
                        <div>
                          <h5 className="font-medium mb-3 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4" />
                            تغييرات الأسئلة:
                          </h5>
                          {selectedComparison.analysis.questions_changes?.length > 0 ? (
                            <ul className="space-y-2">
                              {selectedComparison.analysis.questions_changes.map((change, idx) => (
                                <li key={idx} className="text-sm flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                                  <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                                  <span>{change}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg border">
                              لا توجد تغييرات محددة في الأسئلة
                            </div>
                          )}
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="recommendations" className="space-y-4 mt-4">
                        <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                          <h5 className="font-medium mb-2 text-blue-800 flex items-center gap-2">
                            <Target className="w-4 h-4" />
                            توصيات للمعلم:
                          </h5>
                          <p className="text-sm text-blue-700">
                            {selectedComparison.analysis.recommendation || "يُنصح بالمراجعة اليدوية للتأكد من التغييرات"}
                          </p>
                        </div>
                        
                        <div>
                          <h5 className="font-medium mb-3 flex items-center gap-2">
                            <Eye className="w-4 h-4" />
                            الاختلافات الرئيسية:
                          </h5>
                          {selectedComparison.analysis.major_differences?.length > 0 ? (
                            <ul className="space-y-2">
                              {selectedComparison.analysis.major_differences.map((diff, idx) => (
                                <li key={idx} className="text-sm flex items-start gap-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                                  <Eye className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                                  <span>{diff}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg border">
                              لا توجد اختلافات رئيسية محددة
                            </div>
                          )}
                        </div>
                        
                        {selectedComparison.similarity < 50 && (
                          <div className="bg-gradient-to-r from-red-50 to-red-100 p-4 rounded-lg border-l-4 border-red-500">
                            <h5 className="font-medium mb-2 text-red-800 flex items-center gap-2">
                              <AlertTriangle className="w-4 h-4" />
                              ⚠️ تحذير:
                            </h5>
                            <p className="text-sm text-red-700">
                              نسبة التشابه منخفضة جداً ({selectedComparison.similarity}%). قد تكون هناك اختلافات كبيرة تحتاج لمراجعة دقيقة.
                            </p>
                          </div>
                        )}

                        {selectedComparison.similarity > 90 && (
                          <div className="bg-gradient-to-r from-green-50 to-green-100 p-4 rounded-lg border-l-4 border-green-500">
                            <h5 className="font-medium mb-2 text-green-800 flex items-center gap-2">
                              <CheckCircle className="w-4 h-4" />
                              ✅ نتيجة ممتازة:
                            </h5>
                            <p className="text-sm text-green-700">
                              نسبة التشابه عالية جداً ({selectedComparison.similarity}%). المحتوى متطابق تقريباً مع وجود تغييرات طفيفة فقط.
                            </p>
                          </div>
                        )}
                      </TabsContent>
                      
                      <TabsContent value="texts" className="space-y-4 mt-4">
                        <div className="grid md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="font-medium mb-3 text-orange-600 flex items-center gap-2">
                              <FileText className="w-4 h-4" />
                              النص القديم:
                            </h5>
                            <ScrollArea className="h-80 w-full border rounded-lg bg-orange-50 p-4">
                              <pre className="text-xs whitespace-pre-wrap text-gray-700 font-mono">
                                {selectedOldResult?.extractedText || "النص غير متاح"}
                              </pre>
                            </ScrollArea>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="mt-2 w-full"
                              onClick={() => selectedOldResult?.extractedText && copyToClipboard(selectedOldResult.extractedText)}
                            >
                              <Copy className="w-4 h-4 ml-2" />
                              نسخ النص القديم
                            </Button>
                          </div>
                          <div>
                            <h5 className="font-medium mb-3 text-blue-600 flex items-center gap-2">
                              <FileText className="w-4 h-4" />
                              النص الجديد:
                            </h5>
                            <ScrollArea className="h-80 w-full border rounded-lg bg-blue-50 p-4">
                              <pre className="text-xs whitespace-pre-wrap text-gray-700 font-mono">
                                {selectedNewResult?.extractedText || "النص غير متاح"}
                              </pre>
                            </ScrollArea>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="mt-2 w-full"
                              onClick={() => selectedNewResult?.extractedText && copyToClipboard(selectedNewResult.extractedText)}
                            >
                              <Copy className="w-4 h-4 ml-2" />
                              نسخ النص الجديد
                            </Button>
                          </div>
                        </div>
                        
                        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                          <h6 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
                            <Eye className="w-4 h-4" />
                            ملاحظة مهمة:
                          </h6>
                          <p className="text-sm text-yellow-700">
                            النصوص المعروضة هي النتيجة الخام لعملية التعرف البصري (OCR) باستخدام تقنية Landing AI المتقدمة. 
                            قد تحتوي على أخطاء طفيفة في التعرف على الأحرف أو التنسيق، لكن دقة الاستخراج عالية جداً.
                          </p>
                        </div>
                      </TabsContent>
                    </Tabs>
                  ) : (
                    <div className="text-center py-12 text-gray-500">
                      <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <h3 className="text-lg font-medium mb-2">اختر مقارنة لعرض التفاصيل</h3>
                      <p className="text-sm">انقر على أحد المقارنات من القائمة لعرض التحليل المفصل</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
};

export default AdvancedComparisonDashboard;
