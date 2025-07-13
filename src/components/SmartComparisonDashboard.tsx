/**
 * لوحة المقارنة الذكية المحسنة
 * Enhanced Smart Comparison Dashboard
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Download, 
  FileText, 
  Image, 
  BarChart3, 
  Eye,
  ArrowLeft,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Clock,
  Zap,
  Search,
  Filter,
  Brain,
  Target,
  TrendingUp,
  Layers,
  DollarSign,
  Timer,
  PieChart,
  Activity,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Info,
  Lightbulb,
  Rocket,
  Shield
} from 'lucide-react';
import { toast } from 'sonner';
import SmartBatchService, { 
  SmartBatchRequest, 
  SmartBatchResult, 
  SmartBatchFileResult,
  SmartBatchStats
} from '@/services/smartBatchService';
import { ProcessingSettings } from '@/components/UploadSection';

// Extended interfaces for better type safety
interface ExtendedSmartBatchStats {
  total_pairs: number;
  stage_1_filtered: number;
  stage_2_processed: number;
  stage_3_analyzed: number;
  total_cost_saved: number;
  total_processing_time: number;
  average_similarity: number;
  efficiency_score: number;
  cost_savings_percentage: number;
  savings_percentage?: number;
  processing_speed?: number;
}

interface ExtendedSmartBatchFileResult extends SmartBatchFileResult {
  summary?: string;
  old_text?: string;
  new_text?: string;
}

interface SystemInfo {
  system_name?: string;
  version?: string;
  features?: string[];
  pipeline_stages?: Array<{stage: number; name: string; cost: string; description: string}>;
  expected_savings?: string;
  supported_formats?: string[];
  max_concurrent_workers?: number;
  active_sessions?: number;
}

interface SmartComparisonDashboardProps {
  files?: {old: File[], new: File[]} | null;
  processingSettings?: ProcessingSettings | null;
  onBack: () => void;
}

const SmartComparisonDashboard: React.FC<SmartComparisonDashboardProps> = ({ files, processingSettings, onBack }) => {
  console.log('🚀 SmartComparisonDashboard تم تحميله:', { 
    files: files ? `${files.old.length} + ${files.new.length} ملفات` : 'لا توجد ملفات',
    processingSettings,
    timestamp: new Date().toISOString()
  });
  
  // حالة النظام
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [results, setResults] = useState<SmartBatchResult | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  
  // إعدادات المعالجة - استخدام الإعدادات المرسلة من UploadSection
  const [oldDirectory, setOldDirectory] = useState('../test/2024');
  const [newDirectory, setNewDirectory] = useState('../test/2025');
  const [maxWorkers, setMaxWorkers] = useState(4);
  const [visualThreshold, setVisualThreshold] = useState(0.95);
  const [processingMode, setProcessingMode] = useState<'gemini_only' | 'landingai_gemini'>(
    processingSettings?.processingMode || 'landingai_gemini'
  );
  
  // فلاتر وبحث
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState<'all' | '1' | '2' | '3'>('all');
  const [selectedFile, setSelectedFile] = useState<ExtendedSmartBatchFileResult | null>(null);

  const smartBatchService = SmartBatchService.getInstance();

  // تحديث الإعدادات عند تغيير processingSettings
  useEffect(() => {
    if (processingSettings) {
      setProcessingMode(processingSettings.processingMode);
      setVisualThreshold(processingSettings.visualThreshold / 100); // تحويل من 0-100 إلى 0-1
      console.log('🔧 تم تحديث إعدادات المعالجة:', processingSettings);
    }
  }, [processingSettings]);

  // تحميل معلومات النظام عند بدء التشغيل
  useEffect(() => {
    const loadSystemInfo = async () => {
      try {
        const info = await smartBatchService.getSystemInfo();
        setSystemInfo(info);
      } catch (error) {
        console.error('فشل في تحميل معلومات النظام:', error);
        toast.error('فشل الاتصال بالخادم. يرجى التأكد من تشغيله.');
      }
    };
    
    loadSystemInfo();
    
    return () => {
      smartBatchService.cleanup();
    };
  }, [smartBatchService]);

  // بدء المعالجة التلقائية عند وجود ملفات
  useEffect(() => {
    // التأكد من وجود ملفات وأن المعالجة لم تبدأ بعد
    if (files && files.old.length > 0 && files.new.length > 0 && !isProcessing && !results && !currentSession) {
      console.log('🚀 بدء المعالجة التلقائية للملفات المرفوعة');
      console.log('🔧 إعدادات المعالجة:', {
        processingMode,
        visualThreshold,
        maxWorkers
      });
      
      // تأخير بسيط لإعطاء الواجهة فرصة للرسم قبل بدء العملية المكلفة
      const timer = setTimeout(() => {
        // Define handleStartProcessing inline to avoid declaration order issues
        const startProcessing = async () => {
          try {
            console.log('🚀 بدء المعالجة الذكية...');
            setIsProcessing(true);
            
            let sessionId: string;
            
            // إذا تم تمرير ملفات من واجهة الرفع، استخدمها
            if (files && files.old.length > 0 && files.new.length > 0) {
              console.log('📁 استخدام الملفات المرفوعة:', {
                oldFiles: files.old.map(f => f.name),
                newFiles: files.new.map(f => f.name),
                processingMode,
                visualThreshold
              });
              
              // استخدام الملفات المرفوعة مباشرة مع إعدادات المعالجة
              const response = await smartBatchService.startBatchProcessWithFiles(files.old, files.new, {
                max_workers: maxWorkers,
                visual_threshold: visualThreshold,
                processing_mode: processingMode // إضافة وضع المعالجة
              });
              sessionId = response.session_id;
              setCurrentSession(sessionId);
              
              console.log('✅ تم بدء المعالجة بنجاح:', {
                sessionId: response.session_id,
                response
              });
              
              const modeText = processingMode === 'gemini_only' ? 'Gemini فقط' : 'LandingAI + Gemini';
              toast.success(`تم بدء معالجة ${files.old.length + files.new.length} ملف بوضع ${modeText}! 🚀`);
            } else {
              // استخدام المجلدات (الطريقة القديمة)
              const request: SmartBatchRequest = {
                old_directory: oldDirectory,
                new_directory: newDirectory,
                max_workers: maxWorkers,
                visual_threshold: visualThreshold,
                processing_mode: processingMode // إضافة وضع المعالجة
              };
              
              const response = await smartBatchService.startBatchProcess(request);
              sessionId = response.session_id;
              setCurrentSession(sessionId);
            }
            
            // بدء مراقبة التقدم
            console.log('🔍 بدء مراقبة التقدم للجلسة:', sessionId);
            
            // تحديث فوري للحالة لمنع تجمد الواجهة
            const initialFileCount = files ? files.old.length : 2; // افتراض عدد الملفات إذا لم تكن متاحة
            setResults({
              session_id: sessionId,
              status: 'جاري المعالجة',
              message: 'تم بدء المعالجة الذكية...',
              results: [],
              stats: {
                total_pairs: initialFileCount,
                stage_1_filtered: 0,
                stage_2_processed: 0,
                stage_3_analyzed: 0,
                total_cost_saved: 0,
                total_processing_time: 0,
                average_similarity: 0,
                efficiency_score: 0,
                cost_savings_percentage: 0
              }
            });
            
            smartBatchService.startStatusPolling(sessionId, (result) => {
              console.log('🔄 تحديث النتائج في SmartComparisonDashboard:', {
                status: result.status,
                message: result.message,
                stats: result.stats,
                resultsCount: result.results?.length || 0,
                timestamp: new Date().toISOString()
              });
              
              // تحديث النتائج فورياً لتحديث الواجهة
              setResults(result);
              
              if (result.status === 'مكتمل' || result.status === 'فشل') {
                setIsProcessing(false);
                if (result.status === 'مكتمل') {
                  console.log('✅ اكتملت المعالجة بنجاح!');
                  // التحقق من وجود نتائج فعلية
                  if (result.results && result.results.length > 0) {
                    toast.success('اكتملت المعالجة الذكية بنجاح! 🎉');
                  } else {
                    toast.warning('اكتملت المعالجة لكن لم يتم العثور على ملفات للمقارنة. تأكد من أن الملفات مرتبة بنفس الترتيب.');
                  }
                } else {
                  console.log('❌ فشلت المعالجة');
                  toast.error('فشلت المعالجة الذكية');
                }
              }
            });
            
          } catch (error) {
            setIsProcessing(false);
            console.error('❌ فشل في بدء المعالجة:', error);
            toast.error(`فشل في بدء المعالجة: ${error}`);
          }
        };
        
        startProcessing();
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [files, isProcessing, results, currentSession, maxWorkers, visualThreshold, processingMode, oldDirectory, newDirectory, smartBatchService]);

  // helper normalizer functions
  const getOverallSimilarity = (res: SmartBatchFileResult): number => {
    if (typeof res?.overall_similarity === 'number') return res.overall_similarity;
    if (res?.ai_analysis && typeof res.ai_analysis.similarity_percentage === 'number') {
      return res.ai_analysis.similarity_percentage / 100;
    }
    return 0;
  };
  
  const getVisualSimilarity = (res: SmartBatchFileResult): number | undefined => {
    if (typeof res?.visual_similarity === 'number') return res.visual_similarity;
    return undefined;
  };

  // derive enhancedStats directly from results to avoid type issues
  const enhancedStats = useMemo(() => {
    const s = (results?.stats || {}) as {
      total_pairs?: number;
      stage_1_filtered?: number;
      stage_2_processed?: number;
      stage_3_analyzed?: number;
      total_processing_time?: number;
    };
    const total_pairs = s.total_pairs ?? 0;
    const stage_1_filtered = s.stage_1_filtered ?? 0;
    const stage_2_processed = s.stage_2_processed ?? 0;
    const stage_3_analyzed = s.stage_3_analyzed ?? 0;
    const total_processing_time = s.total_processing_time ?? 0;

    if (total_pairs === 0) return null;

    // احسب متوسط التشابه من النتائج إن وجد
    const similarities = results?.results?.map(getOverallSimilarity) || [];
    const averageSimilarity = similarities.length
      ? (similarities.reduce((a, b) => a + b, 0) / similarities.length) * 100
      : 0;

    const savingsPercentage = smartBatchService.calculateSavingsPercentage({
      total_pairs,
      stage_1_filtered,
      stage_2_processed,
      stage_3_analyzed,
      total_cost_saved: 0,
      total_processing_time,
      average_similarity: averageSimilarity,
      efficiency_score: 0,
      cost_savings_percentage: 0,
    } as SmartBatchStats);

    return {
      total_pairs,
      stage_1_filtered,
      stage_2_processed,
      stage_3_analyzed,
      total_cost_saved: 0,
      total_processing_time,
      average_similarity: averageSimilarity,
      efficiency_score: 0,
      cost_savings_percentage: 0,
      savings_percentage: savingsPercentage,
      processing_speed:
        total_processing_time > 0
          ? total_pairs / (total_processing_time / 60)
          : 0,
    } as ExtendedSmartBatchStats;
  }, [results, smartBatchService]);

  // transform backend results to a common shape for rendering
  const normalizedResults = useMemo(() => {
    if (!results?.results) return [];
    return results.results.map((r: SmartBatchFileResult): ExtendedSmartBatchFileResult => ({
      ...r,
      old_file: r.old_file ?? 'غير معروف',
      new_file: r.new_file ?? 'غير معروف',
      overall_similarity: getOverallSimilarity(r),
      visual_similarity: getVisualSimilarity(r),
      cost_saved: r.cost_saved ?? (r.status === 'تطابق بصري عالي' ? 100 : r.status === 'تم التحليل الكامل' ? 33.3 : 0),
      stage_reached: r.stage_reached ?? (r.status === 'تم التحليل الكامل' ? 3 : 1),
      processing_time: r.processing_time ?? 0,
      status: ['تم التحليل الكامل', 'تطابق بصري عالي'].includes(r.status)
        ? 'completed'
        : r.status === 'فشل'
        ? 'error'
        : 'completed',
    }));
  }, [results]);

  // استخدم normalizedResults بدلاً من results.results
  const filteredResults = useMemo(() => {
    let fr = normalizedResults;

    if (stageFilter !== 'all') {
      const stage = parseInt(stageFilter);
      fr = fr.filter((result) => result.stage_reached >= stage);
    }

    if (searchTerm) {
      fr = fr.filter((result) =>
        result.old_file.toLowerCase().includes(searchTerm.toLowerCase()) ||
        result.new_file.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return fr;
  }, [normalizedResults, stageFilter, searchTerm]);

  // بدء المعالجة الذكية
  const handleStartProcessing = useCallback(async () => {
    try {
      console.log('🚀 بدء المعالجة الذكية...');
      setIsProcessing(true);
      
      let sessionId: string;
      
      // إذا تم تمرير ملفات من واجهة الرفع، استخدمها
      if (files && files.old.length > 0 && files.new.length > 0) {
        console.log('📁 استخدام الملفات المرفوعة:', {
          oldFiles: files.old.map(f => f.name),
          newFiles: files.new.map(f => f.name)
        });
        
        // استخدام الملفات المرفوعة مباشرة
        const response = await smartBatchService.startBatchProcessWithFiles(files.old, files.new, {
          max_workers: maxWorkers,
          visual_threshold: visualThreshold,
          processing_mode: processingMode // إضافة وضع المعالجة
        });
        sessionId = response.session_id;
        setCurrentSession(sessionId);
        
        console.log('✅ تم بدء المعالجة بنجاح:', {
          sessionId: response.session_id,
          response
        });
        
        const modeText = processingMode === 'gemini_only' ? 'Gemini فقط' : 'LandingAI + Gemini';
        toast.success(`تم بدء معالجة ${files.old.length + files.new.length} ملف بوضع ${modeText}! 🚀`);
      } else {
        // استخدام المجلدات (الطريقة القديمة)
        const request: SmartBatchRequest = {
          old_directory: oldDirectory,
          new_directory: newDirectory,
          max_workers: maxWorkers,
          visual_threshold: visualThreshold,
          processing_mode: processingMode // إضافة وضع المعالجة
        };
        
        const response = await smartBatchService.startBatchProcess(request);
        sessionId = response.session_id;
        setCurrentSession(sessionId);
      }
      
      // بدء مراقبة التقدم
      console.log('🔍 بدء مراقبة التقدم للجلسة:', sessionId);
      
      // تحديث فوري للحالة لمنع تجمد الواجهة
      const initialFileCount = files ? files.old.length : 2; // افتراض عدد الملفات إذا لم تكن متاحة
      setResults({
        session_id: sessionId,
        status: 'جاري المعالجة',
        message: 'تم بدء المعالجة الذكية...',
        results: [],
        stats: {
          total_pairs: initialFileCount,
          stage_1_filtered: 0,
          stage_2_processed: 0,
          stage_3_analyzed: 0,
          total_cost_saved: 0,
          total_processing_time: 0,
          average_similarity: 0,
          efficiency_score: 0,
          cost_savings_percentage: 0
        }
      });
      
      smartBatchService.startStatusPolling(sessionId, (result) => {
        console.log('🔄 تحديث النتائج في SmartComparisonDashboard:', {
          status: result.status,
          message: result.message,
          stats: result.stats,
          resultsCount: result.results?.length || 0,
          timestamp: new Date().toISOString()
        });
        
        setResults(result);
        
        if (result.status === 'مكتمل' || result.status === 'فشل') {
          setIsProcessing(false);
          if (result.status === 'مكتمل') {
            console.log('✅ اكتملت المعالجة بنجاح!');
            toast.success('اكتملت المعالجة الذكية بنجاح! 🎉');
          } else {
            console.log('❌ فشلت المعالجة');
            toast.error('فشلت المعالجة الذكية');
          }
        }
      });
      
    } catch (error) {
      setIsProcessing(false);
      console.error('❌ فشل في بدء المعالجة:', error);
      toast.error(`فشل في بدء المعالجة: ${error}`);
    }
  }, [files, maxWorkers, visualThreshold, processingMode, oldDirectory, newDirectory, smartBatchService]);

  // إيقاف المعالجة
  const handleStopProcessing = () => {
    if (currentSession) {
      smartBatchService.stopStatusPolling(currentSession);
      setIsProcessing(false);
      toast.info('تم إيقاف المراقبة');
    }
  };

  // إعادة تشغيل
  const handleRestart = () => {
    // إيقاف المراقبة الحالية قبل إعادة التشغيل
    if (currentSession) {
      smartBatchService.stopStatusPolling(currentSession);
    }
    setResults(null);
    setCurrentSession(null);
    setIsProcessing(false);
    setSelectedFile(null);
  };

  // تنظيف الموارد عند إزالة المكون
  useEffect(() => {
    return () => {
      if (currentSession) {
        smartBatchService.stopStatusPolling(currentSession);
      }
    };
  }, [currentSession, smartBatchService]);

  // رندر مرحلة المعالجة
  const renderProcessingStage = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      <div className="container mx-auto px-6 py-16">
        <div className="max-w-6xl mx-auto">
          
          {/* زر العودة */}
          <div className="mb-6">
            <Button 
              variant="outline" 
              onClick={onBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              العودة لرفع الملفات
            </Button>
          </div>
          
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Brain className="w-8 h-8 text-purple-600" />
              <h2 className="text-3xl font-bold text-gray-900">
                النظام الذكي للمقارنة
              </h2>
            </div>
            <p className="text-lg text-gray-600">
              معالجة ذكية متدرجة لتوفير 35-50% من التكاليف
            </p>
          </div>

          {/* معلومات الملفات المرفوعة */}
          {files && (
            <Card className="mb-8 border-2 border-blue-200 bg-blue-50">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-blue-800 flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    الملفات المرفوعة
                  </h3>
                  <Badge className="bg-blue-600 text-white">
                    {files.old.length + files.new.length} ملف إجمالي
                  </Badge>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-blue-700 mb-2">المنهج القديم ({files.old.length} ملف)</h4>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {files.old.slice(0, 5).map((file, index) => (
                        <div key={index} className="text-sm text-gray-600 flex items-center gap-2">
                          <Image className="w-3 h-3" />
                          {file.name}
                        </div>
                      ))}
                      {files.old.length > 5 && (
                        <div className="text-sm text-gray-500">
                          ... و {files.old.length - 5} ملف آخر
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-blue-700 mb-2">المنهج الجديد ({files.new.length} ملف)</h4>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {files.new.slice(0, 5).map((file, index) => (
                        <div key={index} className="text-sm text-gray-600 flex items-center gap-2">
                          <Image className="w-3 h-3" />
                          {file.name}
                        </div>
                      ))}
                      {files.new.length > 5 && (
                        <div className="text-sm text-gray-500">
                          ... و {files.new.length - 5} ملف آخر
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  {/* إعدادات سريعة */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-700 mb-3">إعدادات المعالجة</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm text-gray-600">عدد المعالجات المتوازية</label>
                        <Input
                          type="number"
                          min="1"
                          max="8"
                          value={maxWorkers}
                          onChange={(e) => setMaxWorkers(parseInt(e.target.value) || 4)}
                          disabled={isProcessing}
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <label className="text-sm text-gray-600">عتبة التشابه البصري</label>
                        <Input
                          type="number"
                          min="0.5"
                          max="1"
                          step="0.05"
                          value={visualThreshold}
                          onChange={(e) => setVisualThreshold(parseFloat(e.target.value) || 0.95)}
                          disabled={isProcessing}
                          className="mt-1"
                        />
                      </div>
                    </div>
                  </div>
                  
                  {!isProcessing && !results && (
                    <div className="text-center">
                      <Button 
                        onClick={handleStartProcessing}
                        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-8 py-3 text-lg font-medium"
                      >
                        <Rocket className="w-5 h-5 ml-2" />
                        إعادة بدء المعالجة
                      </Button>
                    </div>
                  )}
                  
                  {!isProcessing && results && (!results.results || results.results.length === 0) && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                      <div className="flex items-center justify-center gap-2 mb-4">
                        <AlertCircle className="w-6 h-6 text-yellow-600" />
                        <h3 className="text-lg font-semibold text-yellow-800">لا توجد ملفات للمقارنة</h3>
                      </div>
                      <p className="text-yellow-700 mb-4">
                        النظام يقارن الملفات بالترتيب (الملف الأول من المجلد القديم مع الملف الأول من المجلد الجديد، وهكذا).
                        تأكد من أن الملفات مرتبة بنفس الترتيب المطلوب في كلا المجلدين.
                      </p>
                      <div className="flex justify-center gap-4">
                        <Button 
                          onClick={onBack}
                          variant="outline"
                          className="border-yellow-300 text-yellow-700 hover:bg-yellow-100"
                        >
                          <ArrowLeft className="w-4 h-4 ml-2" />
                          العودة لإعادة ترتيب الملفات
                        </Button>
                        <Button 
                          onClick={handleRestart}
                          className="bg-yellow-600 hover:bg-yellow-700 text-white"
                        >
                          <RotateCcw className="w-4 h-4 ml-2" />
                          إعادة المحاولة
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* مراحل المعالجة */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <Card className="border-2 border-green-200 bg-green-50">
              <CardContent className="p-6 text-center">
                <Eye className="w-12 h-12 mx-auto mb-4 text-green-600" />
                <h3 className="text-lg font-bold text-green-800 mb-2">
                  المرحلة 1: المقارنة البصرية
                </h3>
                <p className="text-sm text-green-700 mb-4">
                  مجانية - سريعة - دقيقة 100%
                </p>
                <Badge className="bg-green-100 text-green-800">
                  {enhancedStats?.stage_1_filtered || 0} ملف تم فلترته
                </Badge>
              </CardContent>
            </Card>

            <Card className="border-2 border-orange-200 bg-orange-50">
              <CardContent className="p-6 text-center">
                <Zap className="w-12 h-12 mx-auto mb-4 text-orange-600" />
                <h3 className="text-lg font-bold text-orange-800 mb-2">
                  المرحلة 2: استخراج النص
                </h3>
                <p className="text-sm text-orange-700 mb-4">
                  {processingMode === 'gemini_only' 
                    ? 'Gemini Vision - مباشر - سريع' 
                    : 'LandingAI - سريع - دقة عالية'}
                </p>
                <Badge className="bg-orange-100 text-orange-800">
                  {enhancedStats?.stage_2_processed || 0} ملف معالج
                </Badge>
              </CardContent>
            </Card>

            <Card className="border-2 border-purple-200 bg-purple-50">
              <CardContent className="p-6 text-center">
                <Brain className="w-12 h-12 mx-auto mb-4 text-purple-600" />
                <h3 className="text-lg font-bold text-purple-800 mb-2">
                  المرحلة 3: التحليل الذكي
                </h3>
                <p className="text-sm text-purple-700 mb-4">
                  {processingMode === 'gemini_only' 
                    ? 'Gemini Vision - تحليل مدمج - فوري' 
                    : 'Gemini AI - تحليل عميق - تقارير مفصلة'}
                </p>
                <Badge className="bg-purple-100 text-purple-800">
                  {enhancedStats?.stage_3_analyzed || 0} ملف محلل
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* شريط التقدم الإجمالي */}
          {isProcessing && (
            <Card className="mb-8 border-2 border-blue-200 bg-blue-50">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-blue-800 flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    حالة المعالجة الحالية
                  </h3>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleStopProcessing}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Pause className="w-4 h-4 ml-2" />
                    إيقاف
                  </Button>
                </div>
                
                <div className="space-y-4">
                  {/* شريط التقدم */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-blue-700">
                        {results?.message || 'جاري المعالجة...'}
                      </span>
                      <span className="text-sm text-blue-600">
                        {enhancedStats?.total_pairs ? 
                          `${enhancedStats.stage_1_filtered + enhancedStats.stage_3_analyzed}/${enhancedStats.total_pairs}` : 
                          '0/0'}
                      </span>
                    </div>
                    <Progress 
                      value={enhancedStats?.total_pairs ? 
                        ((enhancedStats.stage_1_filtered + enhancedStats.stage_3_analyzed) / enhancedStats.total_pairs) * 100 : 
                        0} 
                      className="h-3" 
                    />
                  </div>
                  
                  {/* إحصائيات سريعة */}
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-green-50 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {enhancedStats?.stage_1_filtered || 0}
                      </div>
                      <div className="text-xs text-green-700">تطابق بصري</div>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {enhancedStats?.stage_3_analyzed || 0}
                      </div>
                      <div className="text-xs text-purple-700">تحليل عميق</div>
                    </div>
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {enhancedStats?.total_pairs || 0}
                      </div>
                      <div className="text-xs text-blue-700">إجمالي الملفات</div>
                    </div>
                  </div>
                  
                  {/* معلومات الوضع الحالي */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-700 mb-2">الوضع الحالي</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>وضع المعالجة:</span>
                        <span className="font-medium">
                          {processingMode === 'gemini_only' ? 'Gemini فقط' : 'LandingAI + Gemini'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>عتبة التشابه البصري:</span>
                        <span className="font-medium">{(visualThreshold * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>المعالجات المتوازية:</span>
                        <span className="font-medium">{maxWorkers}</span>
                      </div>
                      {enhancedStats?.savings_percentage && (
                        <div className="flex justify-between">
                          <span>نسبة التوفير:</span>
                          <span className="font-medium text-green-600">
                            {enhancedStats.savings_percentage.toFixed(1)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* إحصائيات التوفير */}
          {enhancedStats && (
            <div className="grid md:grid-cols-4 gap-4 mb-8">
              <Card className="bg-gradient-to-r from-green-400 to-green-600 text-white">
                <CardContent className="p-4 text-center">
                  <DollarSign className="w-8 h-8 mx-auto mb-2" />
                  <div className="text-2xl font-bold">
                    {((enhancedStats?.savings_percentage ?? 0).toFixed(1))}%
                  </div>
                  <div className="text-sm opacity-90">توفير في التكلفة</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-blue-400 to-blue-600 text-white">
                <CardContent className="p-4 text-center">
                  <Timer className="w-8 h-8 mx-auto mb-2" />
                  <div className="text-2xl font-bold">
                    {smartBatchService.formatProcessingTime(enhancedStats?.total_processing_time ?? 0)}
                  </div>
                  <div className="text-sm opacity-90">وقت المعالجة</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-purple-400 to-purple-600 text-white">
                <CardContent className="p-4 text-center">
                  <Target className="w-8 h-8 mx-auto mb-2" />
                  <div className="text-2xl font-bold">
                    {((enhancedStats?.average_similarity ?? 0).toFixed(1))}%
                  </div>
                  <div className="text-sm opacity-90">متوسط التشابه</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-r from-orange-400 to-orange-600 text-white">
                <CardContent className="p-4 text-center">
                  <Activity className="w-8 h-8 mx-auto mb-2" />
                  <div className="text-2xl font-bold">
                    {((enhancedStats?.processing_speed ?? 0).toFixed(1))}
                  </div>
                  <div className="text-sm opacity-90">ملف/دقيقة</div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // رندر الإعدادات
  const renderSettings = () => (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          إعدادات المعالجة الذكية
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* إعدادات المجلدات - تظهر فقط عندما لا توجد ملفات مرفوعة */}
        {!files && (
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="oldDir">مجلد الكتب القديمة</Label>
                <Input
                  id="oldDir"
                  value={oldDirectory}
                  onChange={(e) => setOldDirectory(e.target.value)}
                  placeholder="../test/2024"
                />
              </div>
              <div>
                <Label htmlFor="newDir">مجلد الكتب الجديدة</Label>
                <Input
                  id="newDir"
                  value={newDirectory}
                  onChange={(e) => setNewDirectory(e.target.value)}
                  placeholder="../test/2025"
                />
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="workers">عدد المعالجات المتوازية</Label>
                <Input
                  id="workers"
                  type="number"
                  min="1"
                  max="8"
                  value={maxWorkers}
                  onChange={(e) => setMaxWorkers(parseInt(e.target.value) || 4)}
                />
              </div>
              <div>
                <Label htmlFor="threshold">عتبة التشابه البصري</Label>
                <Input
                  id="threshold"
                  type="number"
                  min="0.5"
                  max="1"
                  step="0.05"
                  value={visualThreshold}
                  onChange={(e) => setVisualThreshold(parseFloat(e.target.value) || 0.95)}
                />
              </div>
            </div>
          </div>
        )}
        
        {/* إعدادات المعالجة - تظهر دائماً */}
        {files && (
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div>
              <Label htmlFor="workers">عدد المعالجات المتوازية</Label>
              <Input
                id="workers"
                type="number"
                min="1"
                max="8"
                value={maxWorkers}
                onChange={(e) => setMaxWorkers(parseInt(e.target.value) || 4)}
                disabled={isProcessing}
              />
              <p className="text-xs text-gray-500 mt-1">
                عدد الملفات التي يتم معالجتها بالتوازي
              </p>
            </div>
            <div>
              <Label htmlFor="threshold">عتبة التشابه البصري</Label>
              <Input
                id="threshold"
                type="number"
                min="0.5"
                max="1"
                step="0.05"
                value={visualThreshold}
                onChange={(e) => setVisualThreshold(parseFloat(e.target.value) || 0.95)}
                disabled={isProcessing}
              />
              <p className="text-xs text-gray-500 mt-1">
                إذا كان التشابه البصري أعلى من هذه النسبة، يتم إيقاف المعالجة
              </p>
            </div>
          </div>
        )}
        
        {!files && (
          <div className="flex gap-4">
            <Button 
              onClick={handleStartProcessing} 
              disabled={isProcessing}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            >
              <Rocket className="w-4 h-4 ml-2" />
              بدء المعالجة الذكية
            </Button>
            
            <Button 
              variant="outline" 
              onClick={handleRestart}
              disabled={isProcessing}
            >
              <RotateCcw className="w-4 h-4 ml-2" />
              إعادة تشغيل
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );

  // إذا لم تكن هناك ملفات، أظهر واجهة الإعدادات الأولية
  if (!files) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
        <div className="container mx-auto px-6 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-6">
              <Button 
                variant="outline" 
                onClick={onBack}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                العودة لرفع الملفات
              </Button>
            </div>
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-bold text-center">
                  النظام الذكي للمقارنة
                </CardTitle>
              </CardHeader>
              <CardContent className="p-8 text-center">
                <Brain className="w-20 h-20 mx-auto text-purple-600 mb-6" />
                <p className="text-lg text-gray-600 mb-8">
                  هذه الواجهة تستخدم لمعالجة المجلدات مباشرة من الخادم.
                  <br />
                  للرفع من جهازك، يرجى العودة للواجهة الرئيسية.
                </p>
                {renderSettings()}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  // إذا كان النظام يعالج أو لا توجد نتائج أو النتائج فارغة
  if (isProcessing || !results || !results.results || results.results.length === 0) {
    return renderProcessingStage();
  }

  // رندر النتائج الكاملة
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 ml-2" />
              العودة
            </Button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Brain className="w-6 h-6 text-purple-600" />
                تقرير المقارنة الذكية
              </h1>
              <p className="text-gray-600">
                تم تحليل {enhancedStats?.total_pairs ?? 0} زوج من الملفات بتوفير {enhancedStats?.savings_percentage?.toFixed(1) ?? '0'}% في التكلفة
              </p>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleRestart}>
              <RotateCcw className="w-4 h-4 ml-2" />
              معالجة جديدة
            </Button>
          </div>
        </div>

        {/* إحصائيات سريعة */}
        {enhancedStats && (
          <div className="grid md:grid-cols-5 gap-4 mb-8">
            <Card className="bg-gradient-to-r from-green-400 to-green-600 text-white">
              <CardContent className="p-4 text-center">
                <DollarSign className="w-6 h-6 mx-auto mb-2" />
                <div className="text-xl font-bold">{enhancedStats?.savings_percentage?.toFixed(1) ?? '0'}%</div>
                <div className="text-xs opacity-90">توفير التكلفة</div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-r from-blue-400 to-blue-600 text-white">
              <CardContent className="p-4 text-center">
                <Timer className="w-6 h-6 mx-auto mb-2" />
                <div className="text-xl font-bold">{enhancedStats?.processing_speed?.toFixed(1) ?? '0'}</div>
                <div className="text-xs opacity-90">ملف/دقيقة</div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-r from-purple-400 to-purple-600 text-white">
              <CardContent className="p-4 text-center">
                <Target className="w-6 h-6 mx-auto mb-2" />
                <div className="text-xl font-bold">{enhancedStats?.average_similarity?.toFixed(1) ?? '0'}%</div>
                <div className="text-xs opacity-90">متوسط التشابه</div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-r from-orange-400 to-orange-600 text-white">
              <CardContent className="p-4 text-center">
                <Layers className="w-6 h-6 mx-auto mb-2" />
                <div className="text-xl font-bold">{enhancedStats?.total_pairs ?? 0}</div>
                <div className="text-xs opacity-90">إجمالي الملفات</div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-r from-gray-400 to-gray-600 text-white">
              <CardContent className="p-4 text-center">
                <Clock className="w-6 h-6 mx-auto mb-2" />
                <div className="text-xl font-bold">
                  {smartBatchService.formatProcessingTime(enhancedStats?.total_processing_time ?? 0)}
                </div>
                <div className="text-xs opacity-90">وقت المعالجة</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* فلاتر وبحث */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-64">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="البحث في أسماء الملفات..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button
                  variant={stageFilter === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStageFilter('all')}
                >
                  الكل ({filteredResults.length})
                </Button>
                <Button
                  variant={stageFilter === '1' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStageFilter('1')}
                  className="text-green-600"
                >
                  مرحلة 1 ({enhancedStats?.stage_1_filtered ?? 0})
                </Button>
                <Button
                  variant={stageFilter === '2' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStageFilter('2')}
                  className="text-orange-600"
                >
                  مرحلة 2 ({enhancedStats?.stage_2_processed ?? 0})
                </Button>
                <Button
                  variant={stageFilter === '3' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStageFilter('3')}
                  className="text-purple-600"
                >
                  مرحلة 3 ({enhancedStats?.stage_3_analyzed ?? 0})
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* قائمة النتائج */}
        <div className="grid gap-4">
          {filteredResults.map((result, index) => (
            <Card 
              key={index} 
              className={`cursor-pointer transition-all hover:shadow-lg ${
                selectedFile === result ? 'ring-2 ring-purple-500' : ''
              }`}
              onClick={() => setSelectedFile(result)}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge 
                        className={`
                          ${result.stage_reached === 1 ? 'bg-green-100 text-green-800' : 
                            result.stage_reached === 2 ? 'bg-orange-100 text-orange-800' : 
                            'bg-purple-100 text-purple-800'}
                        `}
                      >
                        المرحلة {result.stage_reached}
                      </Badge>
                      <Badge variant={result.status === 'completed' ? 'default' : 'destructive'}>
                        {result.status === 'completed' ? 'مكتمل' : 'خطأ'}
                      </Badge>
                    </div>
                    
                    <div className="text-sm text-gray-600 mb-2">
                      <span className="font-medium">القديم:</span> {(result?.old_file || '').split('/').pop()}
                      <span className="mx-2">←</span>
                      <span className="font-medium">الجديد:</span> {(result?.new_file || '').split('/').pop()}
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <Target className="w-4 h-4 text-blue-600" />
                        <span className="text-sm">
                          تشابه إجمالي: <span className="font-bold">{((result?.overall_similarity ?? 0) * 100).toFixed(1)}%</span>
                        </span>
                      </div>
                      
                      {result?.visual_similarity && (
                        <div className="flex items-center gap-2">
                          <Eye className="w-4 h-4 text-green-600" />
                          <span className="text-sm">
                            بصري: <span className="font-bold">{((result?.visual_similarity ?? 0) * 100).toFixed(1)}%</span>
                          </span>
                        </div>
                      )}
                      
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">
                          {smartBatchService.formatProcessingTime(result.processing_time)}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-lg font-bold text-green-600">
                      {(result?.cost_saved ?? 0) > 0 ? `${(result?.cost_saved ?? 0).toFixed(1)}% توفير` : 'لا يوجد توفير'}
                    </div>
                    <Progress 
                      value={(result?.overall_similarity ?? 0) * 100} 
                      className="w-32 h-2 mt-2" 
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* تفاصيل الملف المحدد */}
        {selectedFile && (
          <Card className="mt-6 border-2 border-purple-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                تفاصيل المقارنة
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="overview">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="overview">نظرة عامة</TabsTrigger>
                  <TabsTrigger value="visual">المقارنة البصرية</TabsTrigger>
                  <TabsTrigger value="text">استخراج النص</TabsTrigger>
                  <TabsTrigger value="analysis">التحليل الذكي</TabsTrigger>
                </TabsList>
                
                <TabsContent value="overview" className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-bold mb-2">معلومات الملفات</h4>
                      <div className="space-y-2 text-sm">
                        <div><span className="font-medium">الملف القديم:</span> {selectedFile?.old_file ?? '—'}</div>
                        <div><span className="font-medium">الملف الجديد:</span> {selectedFile?.new_file ?? '—'}</div>
                        <div><span className="font-medium">المرحلة المكتملة:</span> {selectedFile?.stage_reached}</div>
                        <div><span className="font-medium">وقت المعالجة:</span> {smartBatchService.formatProcessingTime(selectedFile?.processing_time ?? 0)}</div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-bold mb-2">نتائج التشابه</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>التشابه الإجمالي:</span>
                          <span className="font-bold">{((selectedFile?.overall_similarity ?? 0) * 100).toFixed(1)}%</span>
                        </div>
                        {selectedFile?.visual_similarity && (
                          <div className="flex justify-between">
                            <span>التشابه البصري:</span>
                            <span className="font-bold">{((selectedFile?.visual_similarity ?? 0) * 100).toFixed(1)}%</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span>توفير التكلفة:</span>
                          <span className="font-bold text-green-600">{(selectedFile?.cost_saved ?? 0).toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="visual">
                  <div className="text-center py-8">
                    <Eye className="w-16 h-16 mx-auto mb-4 text-green-600" />
                    <h3 className="text-lg font-bold mb-2">المقارنة البصرية</h3>
                    {selectedFile?.visual_similarity ? (
                      <div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          {((selectedFile?.visual_similarity ?? 0) * 100).toFixed(1)}%
                        </div>
                        <p className="text-gray-600">
                          تم اكتشاف تشابه بصري عالي بدون الحاجة لمعالجة إضافية
                        </p>
                      </div>
                    ) : (
                      <p className="text-gray-600">لم تتم المقارنة البصرية أو لم تكن كافية</p>
                    )}
                  </div>
                </TabsContent>
                
                <TabsContent value="text">
                  <div className="text-center py-8">
                    <Zap className="w-16 h-16 mx-auto mb-4 text-orange-600" />
                    <h3 className="text-lg font-bold mb-2">استخراج النص</h3>
                    {(selectedFile.text_extraction || (selectedFile as ExtendedSmartBatchFileResult).old_text) ? (
                      <div className="text-left space-y-4">
                        <div>
                          <h4 className="font-bold mb-2">النص القديم:</h4>
                          <div className="bg-gray-50 p-4 rounded text-sm max-h-40 overflow-y-auto">
                            {selectedFile.text_extraction?.old_text || (selectedFile as ExtendedSmartBatchFileResult).old_text || 'لا يوجد نص'}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-bold mb-2">النص الجديد:</h4>
                          <div className="bg-gray-50 p-4 rounded text-sm max-h-40 overflow-y-auto">
                            {selectedFile.text_extraction?.new_text || (selectedFile as ExtendedSmartBatchFileResult).new_text || 'لا يوجد نص'}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-600">لم يتم استخراج النص</p>
                    )}
                  </div>
                </TabsContent>
                
                <TabsContent value="analysis">
                  <div className="text-center py-8">
                    <Brain className="w-16 h-16 mx-auto mb-4 text-purple-600" />
                    <h3 className="text-lg font-bold mb-2">التحليل بالذكاء الاصطناعي</h3>
                    {(selectedFile.ai_analysis || selectedFile.summary) ? (
                      <div className="text-left space-y-4">
                        <div className="bg-purple-50 p-4 rounded">
                          <h4 className="font-bold mb-2">الملخص:</h4>
                          <p className="text-sm">{selectedFile.ai_analysis?.summary || selectedFile.summary}</p>
                        </div>
                        
                        {selectedFile.ai_analysis?.content_changes?.length > 0 && (
                          <div>
                            <h4 className="font-bold mb-2">التغييرات المكتشفة:</h4>
                            <ul className="list-disc list-inside space-y-1 text-sm">
                              {selectedFile.ai_analysis?.content_changes?.map((change, idx) => (
                                <li key={idx}>{change}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        <div className="flex justify-between text-sm">
                          <span>نسبة التشابه (AI):</span>
                          <span className="font-bold">{((selectedFile.ai_analysis?.similarity_percentage ?? ((selectedFile.overall_similarity ?? 0)*100)).toFixed(1))}%</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-600">لم يتم التحليل بالذكاء الاصطناعي</p>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default SmartComparisonDashboard; 