import React, { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Eye,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Play,
  Pause,
  RotateCcw,
  BookOpen,
  FileText,
  Image,
  Target,
  CheckCircle2,
  AlertCircle,
  Info,
  RefreshCw,
  Filter,
  Search
} from 'lucide-react';
import { ComparisonResult, ProcessingResult } from '@/services/realAIServices';

interface InteractiveComparisonViewerProps {
  comparisons: ComparisonResult[];
  oldResults: ProcessingResult[];
  newResults: ProcessingResult[];
  onComparisonSelect?: (comparison: ComparisonResult) => void;
}

interface ViewerState {
  selectedIndex: number;
  viewMode: 'side-by-side' | 'overlay' | 'full-screen';
  zoomLevel: number;
  autoPlay: boolean;
  filterMode: 'all' | 'high' | 'medium' | 'low';
  showAnalysis: boolean;
}

export const InteractiveComparisonViewer: React.FC<InteractiveComparisonViewerProps> = ({
  comparisons,
  oldResults,
  newResults,
  onComparisonSelect
}) => {
  const [viewerState, setViewerState] = useState<ViewerState>({
    selectedIndex: 0,
    viewMode: 'side-by-side',
    zoomLevel: 100,
    autoPlay: false,
    filterMode: 'all',
    showAnalysis: true
  });

  const [searchTerm, setSearchTerm] = useState('');

  // فلترة وتصنيف المقارنات
  const filteredComparisons = useMemo(() => {
    let filtered = [...comparisons];

    // تطبيق فلتر البحث
    if (searchTerm) {
      filtered = filtered.filter(comp => 
        comp.oldFileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.newFileName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.analysis.summary?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // تطبيق فلتر مستوى التشابه
    switch (viewerState.filterMode) {
      case 'high':
        filtered = filtered.filter(comp => comp.similarity > 80);
        break;
      case 'medium':
        filtered = filtered.filter(comp => comp.similarity >= 50 && comp.similarity <= 80);
        break;
      case 'low':
        filtered = filtered.filter(comp => comp.similarity < 50);
        break;
    }

    return filtered;
  }, [comparisons, searchTerm, viewerState.filterMode]);

  const currentComparison = filteredComparisons[viewerState.selectedIndex];
  const currentOldResult = oldResults.find(r => r.fileName === currentComparison?.oldFileName);
  const currentNewResult = newResults.find(r => r.fileName === currentComparison?.newFileName);

  // التنقل بين المقارنات
  const navigateComparison = useCallback((direction: 'prev' | 'next') => {
    setViewerState(prev => ({
      ...prev,
      selectedIndex: direction === 'next' 
        ? Math.min(prev.selectedIndex + 1, filteredComparisons.length - 1)
        : Math.max(prev.selectedIndex - 1, 0)
    }));
  }, [filteredComparisons.length]);

  // التشغيل التلقائي
  const toggleAutoPlay = useCallback(() => {
    setViewerState(prev => ({ ...prev, autoPlay: !prev.autoPlay }));
  }, []);

  // تغيير مستوى التكبير
  const adjustZoom = useCallback((delta: number) => {
    setViewerState(prev => ({
      ...prev,
      zoomLevel: Math.max(50, Math.min(200, prev.zoomLevel + delta))
    }));
  }, []);

  // إعادة تعيين العرض
  const resetView = useCallback(() => {
    setViewerState(prev => ({
      ...prev,
      zoomLevel: 100,
      viewMode: 'side-by-side'
    }));
  }, []);

  // التأثيرات للتشغيل التلقائي
  React.useEffect(() => {
    if (viewerState.autoPlay && filteredComparisons.length > 1) {
      const interval = setInterval(() => {
        setViewerState(prev => ({
          ...prev,
          selectedIndex: (prev.selectedIndex + 1) % filteredComparisons.length
        }));
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [viewerState.autoPlay, filteredComparisons.length]);

  // إشعار المكون الأب عند تغيير المقارنة المحددة
  React.useEffect(() => {
    if (currentComparison && onComparisonSelect) {
      onComparisonSelect(currentComparison);
    }
  }, [currentComparison, onComparisonSelect]);

  if (!currentComparison) {
    return (
      <Card className="shadow-lg">
        <CardContent className="p-8 text-center">
          <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-700 mb-2">لا توجد مقارنات للعرض</h3>
          <p className="text-gray-500">قم بتحميل الملفات وبدء عملية المقارنة لعرض النتائج هنا</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* شريط التحكم */}
      <Card className="shadow-lg">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Eye className="w-5 h-5 text-blue-600" />
              عارض المقارنات التفاعلي
            </CardTitle>
            <Badge variant="outline" className="text-sm">
              {viewerState.selectedIndex + 1} من {filteredComparisons.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* البحث والفلترة */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="البحث في المقارنات..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-10 pl-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={viewerState.filterMode}
              onChange={(e) => setViewerState(prev => ({ 
                ...prev, 
                filterMode: e.target.value as 'all' | 'high' | 'medium' | 'low',
                selectedIndex: 0 
              }))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">جميع المستويات</option>
              <option value="high">تشابه عالي (80%+)</option>
              <option value="medium">تشابه متوسط (50-80%)</option>
              <option value="low">تشابه منخفض (&lt;50%)</option>
            </select>
          </div>

          {/* أدوات التحكم */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigateComparison('prev')}
                disabled={viewerState.selectedIndex === 0}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={toggleAutoPlay}
                className={viewerState.autoPlay ? 'bg-blue-50 border-blue-200' : ''}
              >
                {viewerState.autoPlay ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigateComparison('next')}
                disabled={viewerState.selectedIndex === filteredComparisons.length - 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              
              <Separator orientation="vertical" className="h-6" />
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => adjustZoom(-10)}
                disabled={viewerState.zoomLevel <= 50}
              >
                <ZoomOut className="w-4 h-4" />
              </Button>
              
              <span className="text-sm font-medium min-w-12 text-center">
                {viewerState.zoomLevel}%
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => adjustZoom(10)}
                disabled={viewerState.zoomLevel >= 200}
              >
                <ZoomIn className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={resetView}
              >
                <RotateCcw className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={viewerState.viewMode}
                onChange={(e) => setViewerState(prev => ({ 
                  ...prev, 
                  viewMode: e.target.value as 'side-by-side' | 'overlay' | 'full-screen'
                }))}
                className="px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="side-by-side">جنباً إلى جنب</option>
                <option value="overlay">تراكب</option>
                <option value="full-screen">ملء الشاشة</option>
              </select>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewerState(prev => ({ ...prev, showAnalysis: !prev.showAnalysis }))}
                className={viewerState.showAnalysis ? 'bg-purple-50 border-purple-200' : ''}
              >
                <BarChart3 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* شريط تقدم التشابه */}
      <Card className="shadow-lg">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-600" />
              {currentComparison.oldFileName} ↔ {currentComparison.newFileName}
            </h3>
            <div className="flex items-center gap-2">
              {currentComparison.similarity > 90 ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : currentComparison.similarity > 70 ? (
                <Info className="w-5 h-5 text-yellow-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-500" />
              )}
              <Badge 
                className={`text-lg px-4 py-2 ${
                  currentComparison.similarity > 90 ? 'bg-green-500' :
                  currentComparison.similarity > 70 ? 'bg-yellow-500' : 'bg-red-500'
                } text-white`}
              >
                {currentComparison.similarity}%
              </Badge>
            </div>
          </div>
          
          <Progress 
            value={currentComparison.similarity} 
            className="h-4 mb-4" 
          />
          
          <div className="grid grid-cols-3 gap-4 text-center text-sm">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span>المحافظة على المحتوى</span>
            </div>
            <div className="flex items-center gap-2">
              <Minus className="w-4 h-4 text-blue-500" />
              <span>التطوير المتوازن</span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-orange-500" />
              <span>التحديث الشامل</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* المحتوى الرئيسي */}
      <div className={`${viewerState.viewMode === 'full-screen' ? 'fixed inset-0 z-50 bg-white' : ''}`}>
        {viewerState.viewMode === 'full-screen' && (
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-xl font-bold">عرض ملء الشاشة</h2>
            <Button
              variant="outline"
              onClick={() => setViewerState(prev => ({ ...prev, viewMode: 'side-by-side' }))}
            >
              <Minimize2 className="w-4 h-4 ml-2" />
              خروج من ملء الشاشة
            </Button>
          </div>
        )}

        <div className={`${viewerState.viewMode === 'full-screen' ? 'p-4' : ''}`}>
          {viewerState.viewMode === 'side-by-side' ? (
            <div className="grid lg:grid-cols-2 gap-6">
              {/* النص القديم */}
              <Card className="shadow-lg">
                <CardHeader className="bg-gradient-to-r from-orange-50 to-orange-100 border-b">
                  <CardTitle className="flex items-center gap-2 text-orange-700">
                    <BookOpen className="w-5 h-5" />
                    الكتاب القديم
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-96">
                    <div 
                      className="p-6" 
                      style={{ fontSize: `${viewerState.zoomLevel}%` }}
                    >
                      <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                        {currentOldResult?.extractedText || 'النص غير متاح'}
                      </pre>
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* النص الجديد */}
              <Card className="shadow-lg">
                <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 border-b">
                  <CardTitle className="flex items-center gap-2 text-blue-700">
                    <BookOpen className="w-5 h-5" />
                    الكتاب الجديد
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-96">
                    <div 
                      className="p-6" 
                      style={{ fontSize: `${viewerState.zoomLevel}%` }}
                    >
                      <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                        {currentNewResult?.extractedText || 'النص غير متاح'}
                      </pre>
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          ) : viewerState.viewMode === 'overlay' ? (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>عرض التراكب</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="old" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="old" className="flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      النص القديم
                    </TabsTrigger>
                    <TabsTrigger value="new" className="flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      النص الجديد
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="old">
                    <ScrollArea className="h-96">
                      <div 
                        className="p-4" 
                        style={{ fontSize: `${viewerState.zoomLevel}%` }}
                      >
                        <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                          {currentOldResult?.extractedText || 'النص غير متاح'}
                        </pre>
                      </div>
                    </ScrollArea>
                  </TabsContent>
                  
                  <TabsContent value="new">
                    <ScrollArea className="h-96">
                      <div 
                        className="p-4" 
                        style={{ fontSize: `${viewerState.zoomLevel}%` }}
                      >
                        <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                          {currentNewResult?.extractedText || 'النص غير متاح'}
                        </pre>
                      </div>
                    </ScrollArea>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <div className="h-full">
              <ScrollArea className="h-full">
                <div className="grid lg:grid-cols-2 gap-6 h-full">
                  <div 
                    className="p-6 bg-orange-50 rounded-lg" 
                    style={{ fontSize: `${viewerState.zoomLevel}%` }}
                  >
                    <h3 className="font-bold text-orange-700 mb-4">الكتاب القديم</h3>
                    <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                      {currentOldResult?.extractedText || 'النص غير متاح'}
                    </pre>
                  </div>
                  <div 
                    className="p-6 bg-blue-50 rounded-lg" 
                    style={{ fontSize: `${viewerState.zoomLevel}%` }}
                  >
                    <h3 className="font-bold text-blue-700 mb-4">الكتاب الجديد</h3>
                    <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
                      {currentNewResult?.extractedText || 'النص غير متاح'}
                    </pre>
                  </div>
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>

      {/* لوحة التحليل */}
      {viewerState.showAnalysis && viewerState.viewMode !== 'full-screen' && (
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-purple-100 border-b">
            <CardTitle className="flex items-center gap-2 text-purple-700">
              <BarChart3 className="w-5 h-5" />
              تحليل مفصل للمقارنة
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="summary">الملخص</TabsTrigger>
                <TabsTrigger value="changes">التغييرات</TabsTrigger>
                <TabsTrigger value="recommendations">التوصيات</TabsTrigger>
                <TabsTrigger value="stats">الإحصائيات</TabsTrigger>
              </TabsList>
              
              <TabsContent value="summary" className="mt-4">
                <div className="prose max-w-none">
                  <p className="text-gray-700 leading-relaxed">
                    {currentComparison.analysis.summary || 'لا يوجد ملخص متاح'}
                  </p>
                </div>
              </TabsContent>
              
              <TabsContent value="changes" className="mt-4">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium mb-3 text-orange-600">تغييرات المحتوى</h4>
                    <ul className="space-y-2">
                      {currentComparison.analysis.content_changes?.map((change, index) => (
                        <li key={index} className="flex items-start gap-2 p-2 bg-orange-50 rounded">
                          <span className="text-orange-500 mt-1">•</span>
                          <span className="text-sm">{change}</span>
                        </li>
                      )) || <li className="text-gray-500 text-sm">لا توجد تغييرات</li>}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-medium mb-3 text-blue-600">تغييرات الأسئلة</h4>
                    <ul className="space-y-2">
                      {currentComparison.analysis.questions_changes?.map((change, index) => (
                        <li key={index} className="flex items-start gap-2 p-2 bg-blue-50 rounded">
                          <span className="text-blue-500 mt-1">•</span>
                          <span className="text-sm">{change}</span>
                        </li>
                      )) || <li className="text-gray-500 text-sm">لا توجد تغييرات</li>}
                    </ul>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="recommendations" className="mt-4">
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <h4 className="font-medium text-green-800 mb-2">توصيات الخبراء</h4>
                  <p className="text-green-700 text-sm">
                    {currentComparison.analysis.recommendation || 'لا توجد توصيات محددة'}
                  </p>
                </div>
              </TabsContent>
              
              <TabsContent value="stats" className="mt-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{currentComparison.similarity}%</div>
                    <div className="text-xs text-blue-700">نسبة التطابق</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(currentOldResult?.confidence * 100 || 0)}%
                    </div>
                    <div className="text-xs text-green-700">دقة الاستخراج القديم</div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {Math.round(currentNewResult?.confidence * 100 || 0)}%
                    </div>
                    <div className="text-xs text-orange-700">دقة الاستخراج الجديد</div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {currentComparison.analysis.content_changes?.length || 0}
                    </div>
                    <div className="text-xs text-purple-700">عدد التغييرات</div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* شريط التنقل السريع */}
      <Card className="shadow-lg">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">التنقل السريع:</span>
            <div className="flex gap-1">
              {filteredComparisons.slice(0, 10).map((_, index) => (
                <Button
                  key={index}
                  variant={index === viewerState.selectedIndex ? "default" : "outline"}
                  size="sm"
                  className="w-8 h-8 p-0"
                  onClick={() => setViewerState(prev => ({ ...prev, selectedIndex: index }))}
                >
                  {index + 1}
                </Button>
              ))}
              {filteredComparisons.length > 10 && (
                <span className="text-gray-400 text-sm self-center">...</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}; 