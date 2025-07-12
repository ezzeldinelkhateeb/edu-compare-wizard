import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Clock, 
  Zap, 
  Target, 
  TrendingUp, 
  Award, 
  CheckCircle, 
  AlertTriangle,
  BarChart3,
  Activity,
  Gauge,
  Timer,
  Cpu,
  Database
} from 'lucide-react';
import { ComparisonResult, ProcessingResult } from '@/services/realAIServices';

interface PerformanceMetricsProps {
  comparisons: ComparisonResult[];
  oldResults: ProcessingResult[];
  newResults: ProcessingResult[];
  processingTime?: number;
  startTime?: Date;
  endTime?: Date;
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  comparisons,
  oldResults,
  newResults,
  processingTime,
  startTime,
  endTime
}) => {
  const metrics = useMemo(() => {
    const totalFiles = oldResults.length + newResults.length;
    const completedFiles = oldResults.filter(r => r.status === 'completed').length + 
                          newResults.filter(r => r.status === 'completed').length;
    
    const avgSimilarity = comparisons.length > 0 
      ? comparisons.reduce((sum, c) => sum + c.similarity, 0) / comparisons.length 
      : 0;
    
    const avgConfidence = totalFiles > 0 
      ? ([...oldResults, ...newResults].reduce((sum, r) => sum + r.confidence, 0) / totalFiles) * 100
      : 0;
    
    const processingDuration = startTime && endTime 
      ? (endTime.getTime() - startTime.getTime()) / 1000 
      : processingTime || 0;
    
    const filesPerSecond = processingDuration > 0 ? completedFiles / processingDuration : 0;
    
    const qualityScore = (avgSimilarity * 0.4) + (avgConfidence * 0.6);
    
    const distributionData = {
      high: comparisons.filter(c => c.similarity > 80).length,
      medium: comparisons.filter(c => c.similarity >= 50 && c.similarity <= 80).length,
      low: comparisons.filter(c => c.similarity < 50).length
    };

    const efficiencyRating = () => {
      if (qualityScore > 85) return { rating: 'ممتاز', color: 'green', icon: Award };
      if (qualityScore > 70) return { rating: 'جيد جداً', color: 'blue', icon: CheckCircle };
      if (qualityScore > 55) return { rating: 'جيد', color: 'yellow', icon: Target };
      return { rating: 'يحتاج تحسين', color: 'red', icon: AlertTriangle };
    };

    return {
      totalFiles,
      completedFiles,
      avgSimilarity: Math.round(avgSimilarity),
      avgConfidence: Math.round(avgConfidence),
      processingDuration: Math.round(processingDuration),
      filesPerSecond: Math.round(filesPerSecond * 100) / 100,
      qualityScore: Math.round(qualityScore),
      distributionData,
      efficiency: efficiencyRating(),
      successRate: Math.round((completedFiles / totalFiles) * 100),
      estimatedSavings: Math.round((totalFiles * 5) - (processingDuration / 60)) // تقدير الوقت المُوفر (5 دقائق لكل ملف يدوياً)
    };
  }, [comparisons, oldResults, newResults, processingTime, startTime, endTime]);

  return (
    <div className="space-y-6">
      {/* نظرة عامة على الأداء */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-indigo-50 to-indigo-100 border-b">
          <CardTitle className="flex items-center gap-2 text-indigo-700">
            <Activity className="w-5 h-5" />
            مقاييس الأداء والكفاءة
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg">
              <Cpu className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{metrics.filesPerSecond}</div>
              <div className="text-sm opacity-90">ملف/ثانية</div>
            </div>
            
            <div className="text-center p-4 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg">
              <Timer className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{metrics.processingDuration}s</div>
              <div className="text-sm opacity-90">وقت المعالجة</div>
            </div>
            
            <div className="text-center p-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg">
              <Database className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{metrics.avgConfidence}%</div>
              <div className="text-sm opacity-90">دقة الاستخراج</div>
            </div>
            
            <div className="text-center p-4 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg">
              <Gauge className="w-8 h-8 mx-auto mb-2" />
              <div className="text-2xl font-bold">{metrics.qualityScore}%</div>
              <div className="text-sm opacity-90">درجة الجودة</div>
            </div>
          </div>

          {/* تقييم الكفاءة */}
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <metrics.efficiency.icon className={`w-6 h-6 text-${metrics.efficiency.color}-500`} />
                <div>
                  <h4 className="font-medium">تقييم الكفاءة الإجمالية</h4>
                  <p className="text-sm text-gray-600">بناءً على السرعة والدقة والجودة</p>
                </div>
              </div>
              <Badge 
                className={`px-4 py-2 text-lg bg-${metrics.efficiency.color}-500 text-white`}
              >
                {metrics.efficiency.rating}
              </Badge>
            </div>
          </div>

          {/* مؤشرات التقدم */}
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">معدل النجاح</span>
                <span className="text-sm text-gray-600">{metrics.successRate}%</span>
              </div>
              <Progress value={metrics.successRate} className="h-2" />
            </div>
            
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">متوسط التشابه</span>
                <span className="text-sm text-gray-600">{metrics.avgSimilarity}%</span>
              </div>
              <Progress value={metrics.avgSimilarity} className="h-2" />
            </div>
            
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">دقة الاستخراج</span>
                <span className="text-sm text-gray-600">{metrics.avgConfidence}%</span>
              </div>
              <Progress value={metrics.avgConfidence} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* توزيع النتائج */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-green-50 to-green-100 border-b">
          <CardTitle className="flex items-center gap-2 text-green-700">
            <BarChart3 className="w-5 h-5" />
            توزيع نتائج المقارنة
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {metrics.distributionData.high}
              </div>
              <div className="text-sm text-green-700 mb-2">تشابه عالي (80%+)</div>
              <div className="w-full bg-green-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${comparisons.length > 0 ? (metrics.distributionData.high / comparisons.length) * 100 : 0}%` 
                  }}
                ></div>
              </div>
            </div>
            
            <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                {metrics.distributionData.medium}
              </div>
              <div className="text-sm text-yellow-700 mb-2">تشابه متوسط (50-80%)</div>
              <div className="w-full bg-yellow-200 rounded-full h-2">
                <div 
                  className="bg-yellow-500 h-2 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${comparisons.length > 0 ? (metrics.distributionData.medium / comparisons.length) * 100 : 0}%` 
                  }}
                ></div>
              </div>
            </div>
            
            <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="text-3xl font-bold text-red-600 mb-2">
                {metrics.distributionData.low}
              </div>
              <div className="text-sm text-red-700 mb-2">تشابه منخفض (&lt;50%)</div>
              <div className="w-full bg-red-200 rounded-full h-2">
                <div 
                  className="bg-red-500 h-2 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${comparisons.length > 0 ? (metrics.distributionData.low / comparisons.length) * 100 : 0}%` 
                  }}
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* فوائد الأتمتة */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-emerald-50 to-emerald-100 border-b">
          <CardTitle className="flex items-center gap-2 text-emerald-700">
            <TrendingUp className="w-5 h-5" />
            فوائد استخدام الذكاء الاصطناعي
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-emerald-50 rounded-lg">
                <Clock className="w-6 h-6 text-emerald-600" />
                <div>
                  <div className="font-medium">توفير الوقت</div>
                  <div className="text-sm text-emerald-700">
                    وفرت حوالي {metrics.estimatedSavings} دقيقة من العمل اليدوي
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                <Zap className="w-6 h-6 text-blue-600" />
                <div>
                  <div className="font-medium">السرعة</div>
                  <div className="text-sm text-blue-700">
                    معالجة {metrics.filesPerSecond} ملف في الثانية
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                <Target className="w-6 h-6 text-purple-600" />
                <div>
                  <div className="font-medium">الدقة</div>
                  <div className="text-sm text-purple-700">
                    دقة استخراج تصل إلى {metrics.avgConfidence}%
                  </div>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg">
                <h4 className="font-bold mb-2">الأداء الإجمالي</h4>
                <div className="text-3xl font-bold mb-2">{metrics.qualityScore}%</div>
                <div className="text-sm opacity-90">
                  تم معالجة {metrics.completedFiles} من {metrics.totalFiles} ملف بنجاح
                </div>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <h5 className="font-medium mb-2">مقارنة مع المعالجة اليدوية</h5>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="font-bold text-green-600">بالذكاء الاصطناعي</div>
                    <div>{Math.round(metrics.processingDuration / 60)} دقيقة</div>
                  </div>
                  <div>
                    <div className="font-bold text-orange-600">يدوياً (تقدير)</div>
                    <div>{metrics.totalFiles * 5} دقيقة</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* نصائح لتحسين الأداء */}
      {metrics.qualityScore < 70 && (
        <Card className="shadow-lg border-orange-200">
          <CardHeader className="bg-orange-50 border-b">
            <CardTitle className="flex items-center gap-2 text-orange-700">
              <AlertTriangle className="w-5 h-5" />
              نصائح لتحسين الأداء
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <ul className="space-y-2 text-sm">
              {metrics.avgConfidence < 80 && (
                <li className="flex items-start gap-2">
                  <span className="text-orange-500 mt-1">•</span>
                  <span>تأكد من جودة الصور المرفوعة لتحسين دقة الاستخراج</span>
                </li>
              )}
              {metrics.successRate < 90 && (
                <li className="flex items-start gap-2">
                  <span className="text-orange-500 mt-1">•</span>
                  <span>تحقق من تنسيق الملفات المدعومة لتجنب أخطاء المعالجة</span>
                </li>
              )}
              {metrics.avgSimilarity < 60 && (
                <li className="flex items-start gap-2">
                  <span className="text-orange-500 mt-1">•</span>
                  <span>راجع ترتيب الصفحات للتأكد من المقارنة الصحيحة</span>
                </li>
              )}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}; 