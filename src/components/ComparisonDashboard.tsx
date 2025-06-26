
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Download, 
  FileText, 
  BarChart3, 
  Eye, 
  ArrowRight,
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';

interface ComparisonDashboardProps {
  files: {old: File[], new: File[]};
}

const ComparisonDashboard: React.FC<ComparisonDashboardProps> = ({ files }) => {
  const [selectedComparison, setSelectedComparison] = useState(0);
  
  // بيانات وهمية للعرض التوضيحي
  const mockResults = {
    overall: {
      textSimilarity: 78,
      visualSimilarity: 85,
      changesDetected: 23,
      pagesCompared: Math.min(files.old.length, files.new.length)
    },
    changes: [
      {
        type: 'major',
        title: 'تغيير في المحتوى الأساسي',
        description: 'تم تحديث تعريف الجاذبية في الفصل الثالث',
        page: 1,
        confidence: 95
      },
      {
        type: 'minor',
        title: 'تحديث في الأمثلة',
        description: 'تم استبدال المثال القديم بمثال أكثر وضوحاً',
        page: 2,
        confidence: 87
      },
      {
        type: 'format',
        title: 'تعديل في التنسيق',
        description: 'تغيير في حجم الخط ولون العناوين',
        page: 3,
        confidence: 92
      }
    ],
    comparisons: Array.from({ length: Math.min(files.old.length, files.new.length, 5) }, (_, i) => ({
      pageNumber: i + 1,
      oldFile: files.old[i]?.name || `صفحة ${i + 1} قديمة`,
      newFile: files.new[i]?.name || `صفحة ${i + 1} جديدة`,
      similarity: Math.floor(Math.random() * 30) + 70,
      changes: Math.floor(Math.random() * 5) + 1,
      status: Math.random() > 0.3 ? 'changed' : 'identical'
    }))
  };

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'major': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'minor': return <Info className="w-5 h-5 text-yellow-500" />;
      default: return <CheckCircle className="w-5 h-5 text-blue-500" />;
    }
  };

  const getChangeColor = (type: string) => {
    switch (type) {
      case 'major': return 'bg-red-50 border-red-200 text-red-800';
      case 'minor': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default: return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  return (
    <div className="container mx-auto px-6 py-8" dir="rtl">
      {/* الهيدر */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              نتائج المقارنة
            </h1>
            <p className="text-gray-600">
              تم مقارنة {mockResults.overall.pagesCompared} صفحة بنجاح
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              معاينة التقرير
            </Button>
            <Button className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 flex items-center gap-2">
              <Download className="w-4 h-4" />
              تحميل التقرير
            </Button>
          </div>
        </div>

        {/* إحصائيات سريعة */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {mockResults.overall.textSimilarity}%
              </div>
              <div className="text-sm text-blue-700 font-medium">التطابق النصي</div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {mockResults.overall.visualSimilarity}%
              </div>
              <div className="text-sm text-green-700 font-medium">التطابق البصري</div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-bold text-orange-600 mb-2">
                {mockResults.overall.changesDetected}
              </div>
              <div className="text-sm text-orange-700 font-medium">تغييرات مكتشفة</div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <CardContent className="p-6 text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {mockResults.overall.pagesCompared}
              </div>
              <div className="text-sm text-purple-700 font-medium">صفحات مقارنة</div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Tabs defaultValue="comparison" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="comparison" className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            المقارنة التفصيلية
          </TabsTrigger>
          <TabsTrigger value="changes" className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            التغييرات المكتشفة
          </TabsTrigger>
          <TabsTrigger value="statistics" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            الإحصائيات
          </TabsTrigger>
        </TabsList>

        <TabsContent value="comparison" className="space-y-6">
          <div className="grid lg:grid-cols-3 gap-6">
            {/* قائمة الصفحات */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">قائمة الصفحات</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="max-h-96 overflow-y-auto">
                  {mockResults.comparisons.map((comp, index) => (
                    <div
                      key={index}
                      className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedComparison === index ? 'bg-blue-50 border-r-4 border-r-blue-500' : ''
                      }`}
                      onClick={() => setSelectedComparison(index)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">صفحة {comp.pageNumber}</span>
                        <Badge variant={comp.status === 'changed' ? 'destructive' : 'secondary'}>
                          {comp.status === 'changed' ? 'متغيرة' : 'متطابقة'}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        التشابه: {comp.similarity}%
                      </div>
                      <Progress value={comp.similarity} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* المقارنة المرئية */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>المقارنة المرئية - صفحة {mockResults.comparisons[selectedComparison]?.pageNumber}</span>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setSelectedComparison(Math.max(0, selectedComparison - 1))}
                      disabled={selectedComparison === 0}
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setSelectedComparison(Math.min(mockResults.comparisons.length - 1, selectedComparison + 1))}
                      disabled={selectedComparison === mockResults.comparisons.length - 1}
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-700">المنهج القديم</h4>
                    <div className="aspect-[3/4] bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
                      <div className="text-center text-gray-500">
                        <FileText className="w-12 h-12 mx-auto mb-2" />
                        <p className="text-sm">
                          {mockResults.comparisons[selectedComparison]?.oldFile}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-700">المنهج الجديد</h4>
                    <div className="aspect-[3/4] bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
                      <div className="text-center text-gray-500">
                        <FileText className="w-12 h-12 mx-auto mb-2" />
                        <p className="text-sm">
                          {mockResults.comparisons[selectedComparison]?.newFile}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">نسبة التشابه:</span>
                    <span className="text-2xl font-bold text-blue-600">
                      {mockResults.comparisons[selectedComparison]?.similarity}%
                    </span>
                  </div>
                  <Progress 
                    value={mockResults.comparisons[selectedComparison]?.similarity} 
                    className="mt-2 h-3"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="changes" className="space-y-6">
          <div className="space-y-4">
            {mockResults.changes.map((change, index) => (
              <Card key={index} className={`border-r-4 ${getChangeColor(change.type)}`}>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    {getChangeIcon(change.type)}
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-semibold">{change.title}</h3>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">صفحة {change.page}</Badge>
                          <Badge variant="secondary">{change.confidence}% دقة</Badge>
                        </div>
                      </div>
                      <p className="text-gray-600 mb-4">{change.description}</p>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm">
                          عرض التفاصيل
                        </Button>
                        <Button variant="ghost" size="sm">
                          الانتقال للصفحة
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="statistics" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>توزيع التغييرات</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      تغييرات رئيسية
                    </span>
                    <span className="font-bold">8</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                      تغييرات ثانوية
                    </span>
                    <span className="font-bold">12</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      تغييرات تنسيق
                    </span>
                    <span className="font-bold">3</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>الأداء والدقة</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>دقة التحليل النصي</span>
                      <span className="font-bold">95%</span>
                    </div>
                    <Progress value={95} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>دقة التحليل البصري</span>
                      <span className="font-bold">92%</span>
                    </div>
                    <Progress value={92} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>وقت المعالجة</span>
                      <span className="font-bold">28 ثانية</span>
                    </div>
                    <Progress value={85} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ComparisonDashboard;
