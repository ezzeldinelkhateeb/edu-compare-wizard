/**
 * لوحة تحكم المقارنة السريعة مع المعالجة المتوازية
 * Ultra Fast Comparison Dashboard with Parallel Processing
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Upload,
  Zap,
  Clock,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  XCircle,
  Play,
  Square,
  RotateCcw,
  Download,
  Eye,
  BarChart3,
  Cpu,
  Timer
} from 'lucide-react';
import { toast } from 'sonner';

import UltraFastComparisonService, {
  UltraFastComparisonResult,
  ComparisonStatus
} from '@/services/ultraFastComparisonService';

interface ProcessingStats {
  textExtractionTime: number;
  visualComparisonTime: number;
  geminiAnalysisTime: number;
  totalParallelTime: number;
  parallelEfficiency: number;
  speedImprovement: number;
}

const UltraFastComparisonDashboard: React.FC = () => {
  // State variables
  const [oldImage, setOldImage] = useState<File | null>(null);
  const [newImage, setNewImage] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<ComparisonStatus | null>(null);
  const [result, setResult] = useState<UltraFastComparisonResult | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [processingStats, setProcessingStats] = useState<ProcessingStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const oldImageInputRef = useRef<HTMLInputElement>(null);
  const newImageInputRef = useRef<HTMLInputElement>(null);
  const comparisonService = UltraFastComparisonService.getInstance();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      comparisonService.cleanup();
    };
  }, []);

  // Handle file selection
  const handleFileSelect = useCallback((file: File, type: 'old' | 'new') => {
    if (type === 'old') {
      setOldImage(file);
    } else {
      setNewImage(file);
    }
    setError(null);
  }, []);

  // Handle status updates
  const handleStatusUpdate = useCallback((status: ComparisonStatus) => {
    setCurrentStatus(status);
    
    // Show progress toast
    if (status.status === 'processing') {
      toast.loading(`${status.message} (${status.progress}%)`, {
        id: `status-${status.session_id}`,
      });
    } else if (status.status === 'completed') {
      toast.success('اكتملت المقارنة بنجاح! 🎉', {
        id: `status-${status.session_id}`,
      });
    } else if (status.status === 'failed') {
      toast.error(`فشلت المقارنة: ${status.error}`, {
        id: `status-${status.session_id}`,
      });
    }
  }, []);

  // Calculate processing stats
  const calculateStats = useCallback((result: UltraFastComparisonResult): ProcessingStats => {
    const textExtractionTime = 
      result.old_text_extraction.processing_time + 
      result.new_text_extraction.processing_time;
    
    const visualComparisonTime = result.visual_comparison.processing_time;
    const geminiAnalysisTime = result.gemini_analysis.processing_time;
    const totalParallelTime = result.total_processing_time;
    
    // Calculate sequential time (if run one after another)
    const sequentialTime = textExtractionTime + visualComparisonTime + geminiAnalysisTime;
    
    const parallelEfficiency = result.parallel_efficiency;
    const speedImprovement = comparisonService.calculateSpeedImprovement(
      totalParallelTime, 
      sequentialTime
    );

    return {
      textExtractionTime,
      visualComparisonTime,
      geminiAnalysisTime,
      totalParallelTime,
      parallelEfficiency,
      speedImprovement
    };
  }, [comparisonService]);

  // Start comparison
  const startComparison = useCallback(async () => {
    if (!oldImage || !newImage) {
      toast.error('يرجى اختيار كلا الصورتين أولاً');
      return;
    }

    try {
      setIsProcessing(true);
      setError(null);
      setResult(null);
      setCurrentStatus(null);
      setProcessingStats(null);

      const comparisonResult = await comparisonService.performFullComparison(
        oldImage,
        newImage,
        handleStatusUpdate
      );

      setResult(comparisonResult);
      setSessionId(comparisonResult.session_id);
      
      const stats = calculateStats(comparisonResult);
      setProcessingStats(stats);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      setError(errorMessage);
      toast.error(`فشلت المقارنة: ${errorMessage}`);
    } finally {
      setIsProcessing(false);
    }
  }, [oldImage, newImage, comparisonService, handleStatusUpdate, calculateStats]);

  // Cancel comparison
  const cancelComparison = useCallback(async () => {
    if (!sessionId) return;

    try {
      await comparisonService.cancelComparison(sessionId);
      setIsProcessing(false);
      setCurrentStatus(null);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'خطأ غير معروف';
      toast.error(`فشل في إلغاء المقارنة: ${errorMessage}`);
    }
  }, [sessionId, comparisonService]);

  // Reset all
  const resetComparison = useCallback(() => {
    setOldImage(null);
    setNewImage(null);
    setIsProcessing(false);
    setCurrentStatus(null);
    setResult(null);
    setSessionId(null);
    setProcessingStats(null);
    setError(null);
    
    if (oldImageInputRef.current) oldImageInputRef.current.value = '';
    if (newImageInputRef.current) newImageInputRef.current.value = '';
  }, []);

  // Get status icon
  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  // Get stage name in Arabic
  const getStageNameArabic = (stage?: string) => {
    switch (stage) {
      case 'initialization':
        return 'تهيئة النظام';
      case 'parallel_extraction':
        return 'استخراج النص المتوازي';
      case 'gemini_analysis':
        return 'تحليل Gemini';
      default:
        return stage || 'غير محدد';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6" dir="rtl">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <Zap className="h-8 w-8 text-yellow-500" />
          المقارنة السريعة المتوازية
        </h1>
        <p className="text-gray-600">
          مقارنة الصور باستخدام المعالجة المتوازية لأقصى سرعة ممكنة
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            رفع الصور
          </CardTitle>
          <CardDescription>
            اختر الصورتين المراد مقارنتهما
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Old Image Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium">الصورة القديمة</label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                <input
                  ref={oldImageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0], 'old')}
                  className="hidden"
                  disabled={isProcessing}
                />
                <Button
                  variant="outline"
                  onClick={() => oldImageInputRef.current?.click()}
                  disabled={isProcessing}
                  className="w-full"
                >
                  {oldImage ? oldImage.name : 'اختر الصورة القديمة'}
                </Button>
              </div>
            </div>

            {/* New Image Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium">الصورة الجديدة</label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                <input
                  ref={newImageInputRef}
                  type="file"
                  accept="image/*"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0], 'new')}
                  className="hidden"
                  disabled={isProcessing}
                />
                <Button
                  variant="outline"
                  onClick={() => newImageInputRef.current?.click()}
                  disabled={isProcessing}
                  className="w-full"
                >
                  {newImage ? newImage.name : 'اختر الصورة الجديدة'}
                </Button>
              </div>
            </div>
          </div>

          <Separator className="my-4" />

          {/* Action Buttons */}
          <div className="flex justify-center gap-4">
            <Button
              onClick={startComparison}
              disabled={!oldImage || !newImage || isProcessing}
              className="flex items-center gap-2"
              size="lg"
            >
              {isProcessing ? (
                <>
                  <Clock className="h-4 w-4 animate-spin" />
                  جاري المعالجة...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  بدء المقارنة السريعة
                </>
              )}
            </Button>

            {isProcessing && (
              <Button
                variant="destructive"
                onClick={cancelComparison}
                className="flex items-center gap-2"
              >
                <Square className="h-4 w-4" />
                إلغاء
              </Button>
            )}

            <Button
              variant="outline"
              onClick={resetComparison}
              disabled={isProcessing}
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              إعادة تعيين
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Processing Status */}
      {currentStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon(currentStatus.status)}
              حالة المعالجة
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">المرحلة:</span>
              <Badge variant="outline">
                {getStageNameArabic(currentStatus.stage)}
              </Badge>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>{currentStatus.message}</span>
                <span>{currentStatus.progress}%</span>
              </div>
              <Progress value={currentStatus.progress} className="w-full" />
            </div>

            {currentStatus.current_file && (
              <div className="text-sm text-gray-600">
                الملف الحالي: {currentStatus.current_file}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <Tabs defaultValue="summary" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="summary">الملخص</TabsTrigger>
            <TabsTrigger value="performance">الأداء</TabsTrigger>
            <TabsTrigger value="details">التفاصيل</TabsTrigger>
            <TabsTrigger value="text">النصوص</TabsTrigger>
          </TabsList>

          {/* Summary Tab */}
          <TabsContent value="summary">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  ملخص النتائج
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center space-y-2">
                        <Eye className="h-8 w-8 mx-auto text-blue-500" />
                        <div className="text-2xl font-bold">
                          {(result.overall_similarity * 100).toFixed(1)}%
                        </div>
                        <p className="text-sm text-gray-600">التشابه الإجمالي</p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center space-y-2">
                        <Timer className="h-8 w-8 mx-auto text-green-500" />
                        <div className="text-2xl font-bold">
                          {comparisonService.formatProcessingTime(result.total_processing_time)}
                        </div>
                        <p className="text-sm text-gray-600">وقت المعالجة</p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-center space-y-2">
                        <Cpu className="h-8 w-8 mx-auto text-purple-500" />
                        <div className="text-2xl font-bold">
                          {result.parallel_efficiency.toFixed(1)}%
                        </div>
                        <p className="text-sm text-gray-600">كفاءة المعالجة</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <Separator />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold mb-2">التشابه البصري</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>SSIM:</span>
                        <span>{(result.visual_comparison.ssim_score * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>التشابه العام:</span>
                        <span>{(result.visual_comparison.similarity * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">تحليل النص</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span>التشابه النصي:</span>
                        <span>{result.gemini_analysis.similarity_percentage}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>عدد التغييرات:</span>
                        <span>{result.gemini_analysis.content_changes.length}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  إحصائيات الأداء
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {processingStats && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Card>
                        <CardContent className="pt-6">
                          <h4 className="font-semibold mb-3">أوقات المعالجة</h4>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span>استخراج النص:</span>
                              <span>{comparisonService.formatProcessingTime(processingStats.textExtractionTime)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>المقارنة البصرية:</span>
                              <span>{comparisonService.formatProcessingTime(processingStats.visualComparisonTime)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>تحليل Gemini:</span>
                              <span>{comparisonService.formatProcessingTime(processingStats.geminiAnalysisTime)}</span>
                            </div>
                            <Separator />
                            <div className="flex justify-between font-semibold">
                              <span>الإجمالي المتوازي:</span>
                              <span>{comparisonService.formatProcessingTime(processingStats.totalParallelTime)}</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardContent className="pt-6">
                          <h4 className="font-semibold mb-3">التحسينات</h4>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span>كفاءة المعالجة:</span>
                              <span className="text-green-600 font-semibold">
                                {processingStats.parallelEfficiency.toFixed(1)}%
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span>تحسن السرعة:</span>
                              <span className="text-blue-600 font-semibold">
                                {processingStats.speedImprovement.toFixed(1)}%
                              </span>
                            </div>
                            <div className="text-sm text-gray-600 mt-2">
                              المعالجة المتوازية أسرع بـ {(processingStats.speedImprovement / 100 + 1).toFixed(1)}x
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    <Progress 
                      value={processingStats.parallelEfficiency} 
                      className="w-full h-3"
                    />
                    <p className="text-center text-sm text-gray-600">
                      كفاءة المعالجة المتوازية: {processingStats.parallelEfficiency.toFixed(1)}%
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Details Tab */}
          <TabsContent value="details">
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>تفاصيل استخراج النص</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold mb-2">الصورة القديمة</h4>
                      <div className="space-y-1 text-sm">
                        <div>الخدمة: {result.old_text_extraction.service}</div>
                        <div>عدد الكلمات: {result.old_text_extraction.word_count}</div>
                        <div>الثقة: {(result.old_text_extraction.confidence * 100).toFixed(1)}%</div>
                        <div>الوقت: {comparisonService.formatProcessingTime(result.old_text_extraction.processing_time)}</div>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">الصورة الجديدة</h4>
                      <div className="space-y-1 text-sm">
                        <div>الخدمة: {result.new_text_extraction.service}</div>
                        <div>عدد الكلمات: {result.new_text_extraction.word_count}</div>
                        <div>الثقة: {(result.new_text_extraction.confidence * 100).toFixed(1)}%</div>
                        <div>الوقت: {comparisonService.formatProcessingTime(result.new_text_extraction.processing_time)}</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>ملخص Gemini</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">{result.gemini_analysis.summary}</p>
                  {result.gemini_analysis.content_changes.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-semibold mb-2">التغييرات المكتشفة:</h4>
                      <ul className="list-disc list-inside text-sm space-y-1">
                        {result.gemini_analysis.content_changes.map((change, index) => (
                          <li key={index}>{change}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Text Tab */}
          <TabsContent value="text">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>النص المستخرج - الصورة القديمة</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-96 overflow-y-auto p-4 bg-gray-50 rounded text-sm whitespace-pre-wrap">
                    {result.old_text_extraction.text || 'لم يتم استخراج نص'}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>النص المستخرج - الصورة الجديدة</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-96 overflow-y-auto p-4 bg-gray-50 rounded text-sm whitespace-pre-wrap">
                    {result.new_text_extraction.text || 'لم يتم استخراج نص'}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export default UltraFastComparisonDashboard; 