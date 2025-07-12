import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { LanguageSelector, useLanguageSelection } from './LanguageSelector';
import { useBatchProcessing } from '../hooks/useBatchProcessing';
import { multilingualServices } from '../services/multilingualServices';
import {
  Upload,
  FolderOpen,
  FileText,
  Trash2,
  Download,
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
  Info,
  Languages,
  Settings,
  BarChart3
} from 'lucide-react';

interface BatchProcessingDashboardProps {
  onResultsReady?: (results: unknown) => void;
}

export function BatchProcessingDashboard({ onResultsReady }: BatchProcessingDashboardProps) {
  const {
    selectedLanguage,
    setSelectedLanguage,
    detectedLanguage,
    confidence,
    updateDetection,
    resetDetection
  } = useLanguageSelection();

  const {
    files,
    isUploading,
    isProcessing,
    currentPhase,
    uploadProgress,
    processingProgress,
    statistics,
    summary,
    error,
    addFiles,
    removeFile,
    clearFiles,
    processFiles,
    getResults,
    cleanup,
    validateFiles
  } = useBatchProcessing();

  const [processingOptions, setProcessingOptions] = useState({
    enableLandingAI: true,
    enableGemini: true,
    outputFormat: 'json' as 'json' | 'markdown' | 'both',
    maxConcurrent: 5
  });

  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle file selection
  const handleFileSelection = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    
    if (selectedFiles.length === 0) return;

    // Validate files
    const { valid, invalid } = validateFiles(selectedFiles);
    
    if (invalid.length > 0) {
      // Show error for invalid files
      const invalidNames = invalid.map(f => f.name).join(', ');
      alert(`الملفات التالية غير مدعومة: ${invalidNames}`);
    }

    if (valid.length > 0) {
      addFiles(valid);
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [addFiles, validateFiles]);

  // Handle drag and drop
  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const droppedFiles = Array.from(event.dataTransfer.files);
    
    const { valid, invalid } = validateFiles(droppedFiles);
    
    if (invalid.length > 0) {
      const invalidNames = invalid.map(f => f.name).join(', ');
      alert(`الملفات التالية غير مدعومة: ${invalidNames}`);
    }

    if (valid.length > 0) {
      addFiles(valid);
    }
  }, [addFiles, validateFiles]);

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
  }, []);

  // Start processing
  const handleStartProcessing = useCallback(async () => {
    const options = {
      languagePreference: selectedLanguage === 'auto' ? undefined : selectedLanguage,
      enableLandingAI: processingOptions.enableLandingAI,
      enableGemini: processingOptions.enableGemini,
      maxConcurrent: processingOptions.maxConcurrent,
      outputFormat: processingOptions.outputFormat
    };

    const success = await processFiles(options);
    
    if (success && onResultsReady) {
      const results = await getResults();
      if (results) {
        onResultsReady(results);
      }
    }
  }, [selectedLanguage, processingOptions, processFiles, getResults, onResultsReady]);

  // Get status color for file
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'processing': return 'text-blue-600';
      case 'uploading': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed': return <AlertTriangle className="h-4 w-4 text-red-600" />;
      case 'processing': return <Clock className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'uploading': return <Upload className="h-4 w-4 text-yellow-600" />;
      default: return <FileText className="h-4 w-4 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    return multilingualServices.formatFileSize(bytes);
  };

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold flex items-center justify-center gap-2">
          <FolderOpen className="h-8 w-8" />
          المعالجة المجمعة للملفات
        </h1>
        <p className="text-muted-foreground">
          معالج متقدم لتحليل ومقارنة عدة ملفات في دفعة واحدة مع دعم اللغات المتعددة
        </p>
      </div>

      {/* Language Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Languages className="h-5 w-5" />
            إعدادات اللغة والمعالجة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <LanguageSelector
                selectedLanguage={selectedLanguage}
                onLanguageChange={setSelectedLanguage}
                showDetectionStatus={!!detectedLanguage}
                detectedLanguage={detectedLanguage}
                confidence={confidence}
              />
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">خيارات متقدمة</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  {showAdvancedOptions ? 'إخفاء' : 'إظهار'}
                </Button>
              </div>
              
              {showAdvancedOptions && (
                <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={processingOptions.enableLandingAI}
                      onChange={(e) => setProcessingOptions(prev => ({
                        ...prev,
                        enableLandingAI: e.target.checked
                      }))}
                      className="rounded"
                    />
                    <span className="text-sm">Landing AI</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={processingOptions.enableGemini}
                      onChange={(e) => setProcessingOptions(prev => ({
                        ...prev,
                        enableGemini: e.target.checked
                      }))}
                      className="rounded"
                    />
                    <span className="text-sm">Gemini Analysis</span>
                  </label>
                  
                  <div className="col-span-2">
                    <label className="text-sm font-medium">تنسيق الإخراج:</label>
                    <select
                      value={processingOptions.outputFormat}
                      onChange={(e) => setProcessingOptions(prev => ({
                        ...prev,
                        outputFormat: e.target.value as 'json' | 'markdown' | 'both'
                      }))}
                      className="w-full mt-1 p-2 border rounded"
                    >
                      <option value="json">JSON</option>
                      <option value="markdown">Markdown</option>
                      <option value="both">كلاهما</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="upload" value={currentPhase === 'idle' ? 'upload' : 'processing'}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload">رفع الملفات</TabsTrigger>
          <TabsTrigger value="processing">المعالجة</TabsTrigger>
          <TabsTrigger value="results">النتائج</TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>اختيار الملفات</span>
                {files.length > 0 && (
                  <Badge variant="outline">{files.length} ملف محدد</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* File Drop Zone */}
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-gray-400 transition-colors"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".jpg,.jpeg,.png,.pdf,.md,.txt,.docx"
                  onChange={handleFileSelection}
                  className="hidden"
                />
                
                <FolderOpen className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium mb-2">اختر ملفات للمعالجة</h3>
                <p className="text-gray-600 mb-4">
                  اضغط لاختيار الملفات أو اسحب وأفلت الملفات هنا
                </p>
                <p className="text-sm text-gray-400">
                  الأنواع المدعومة: JPG, PNG, PDF, MD, TXT, DOCX
                </p>
              </div>

              {/* Selected Files List */}
              {files.length > 0 && (
                <div className="mt-6 space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">الملفات المحددة:</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearFiles}
                      disabled={isUploading || isProcessing}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      مسح الكل
                    </Button>
                  </div>
                  
                  <div className="max-h-60 overflow-y-auto space-y-2">
                    {files.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          {getStatusIcon(file.status)}
                          <div className="flex-1">
                            <p className="text-sm font-medium">{file.file.name}</p>
                            <p className="text-xs text-gray-500">
                              {formatFileSize(file.file.size)}
                            </p>
                          </div>
                          <div className="text-right">
                            <Badge
                              variant={file.status === 'completed' ? 'default' : 
                                     file.status === 'failed' ? 'destructive' : 'secondary'}
                              className="text-xs"
                            >
                              {file.status === 'completed' ? 'مكتمل' :
                               file.status === 'failed' ? 'فشل' :
                               file.status === 'processing' ? 'جاري المعالجة' :
                               file.status === 'uploading' ? 'جاري الرفع' : 'في الانتظار'}
                            </Badge>
                          </div>
                        </div>
                        
                        {file.status === 'pending' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(file.id)}
                            disabled={isUploading || isProcessing}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Start Processing Button */}
              {files.length > 0 && (
                <div className="mt-6">
                  <Button
                    onClick={handleStartProcessing}
                    disabled={isUploading || isProcessing || files.length === 0}
                    className="w-full h-12"
                    size="lg"
                  >
                    {isUploading || isProcessing ? (
                      <>
                        <Clock className="mr-2 h-5 w-5 animate-spin" />
                        {isUploading ? 'جاري الرفع...' : 'جاري المعالجة...'}
                      </>
                    ) : (
                      <>
                        <Zap className="mr-2 h-5 w-5" />
                        ابدأ المعالجة ({files.length} ملف)
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Processing Tab */}
        <TabsContent value="processing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                حالة المعالجة
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Overall Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>التقدم العام</span>
                  <span>
                    {statistics.completed}/{statistics.total} ({Math.round(statistics.completionRate)}%)
                  </span>
                </div>
                <Progress value={statistics.completionRate} className="h-2" />
              </div>

              {/* Statistics */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{statistics.completed}</div>
                  <div className="text-sm text-green-800">مكتمل</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{statistics.processing}</div>
                  <div className="text-sm text-blue-800">قيد المعالجة</div>
                </div>
                <div className="text-center p-3 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">{statistics.pending}</div>
                  <div className="text-sm text-yellow-800">في الانتظار</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{statistics.failed}</div>
                  <div className="text-sm text-red-800">فشل</div>
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-800">
                    {error}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  نتائج المعالجة
                </span>
                {summary && (
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    تحميل التقرير
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summary ? (
                <div className="space-y-4">
                  {/* Summary Statistics */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="text-center p-3 border rounded-lg">
                      <div className="text-lg font-semibold">
                        {(summary as any)?.batch_summary?.total_files || statistics.total}
                      </div>
                      <div className="text-sm text-muted-foreground">إجمالي الملفات</div>
                    </div>
                    <div className="text-center p-3 border rounded-lg">
                      <div className="text-lg font-semibold text-green-600">
                        {(summary as any)?.batch_summary?.successful_files || statistics.completed}
                      </div>
                      <div className="text-sm text-muted-foreground">نجح</div>
                    </div>
                    <div className="text-center p-3 border rounded-lg">
                      <div className="text-lg font-semibold text-red-600">
                        {(summary as any)?.batch_summary?.failed_files || statistics.failed}
                      </div>
                      <div className="text-sm text-muted-foreground">فشل</div>
                    </div>
                    <div className="text-center p-3 border rounded-lg">
                      <div className="text-lg font-semibold">
                        {Math.round((summary as any)?.batch_summary?.success_rate || statistics.completionRate)}%
                      </div>
                      <div className="text-sm text-muted-foreground">معدل النجاح</div>
                    </div>
                  </div>

                  {/* Language Distribution */}
                  {(summary as any)?.language_distribution && (
                    <div>
                      <h4 className="font-medium mb-2">توزيع اللغات:</h4>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries((summary as any).language_distribution).map(([lang, count]) => (
                          <Badge key={lang} variant="outline">
                            {multilingualServices.getLanguageDisplayName(lang)}: {count as number}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Info className="h-8 w-8 mx-auto mb-2" />
                  <p>لا توجد نتائج بعد. ابدأ بمعالجة بعض الملفات.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 