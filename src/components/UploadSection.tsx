
import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, FileText, FolderOpen, AlertCircle, CheckCircle2, Zap } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface UploadSectionProps {
  onFilesUploaded: (files: {old: File[], new: File[]}) => void;
}

const UploadSection: React.FC<UploadSectionProps> = ({ onFilesUploaded }) => {
  const [dragActive, setDragActive] = useState<'old' | 'new' | null>(null);
  const [oldFiles, setOldFiles] = useState<File[]>([]);
  const [newFiles, setNewFiles] = useState<File[]>([]);
  const { toast } = useToast();

  const handleDrag = useCallback((e: React.DragEvent, type: 'old' | 'new') => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(type);
    } else if (e.type === "dragleave") {
      setDragActive(null);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, type: 'old' | 'new') => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(null);

    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(file => 
      file.type.startsWith('image/') || file.type === 'application/pdf'
    );

    if (validFiles.length !== files.length) {
      toast({
        title: "تحذير",
        description: "بعض الملفات غير مدعومة. يُقبل فقط الصور وملفات PDF",
        variant: "destructive"
      });
    }

    if (type === 'old') {
      setOldFiles(prev => [...prev, ...validFiles]);
    } else {
      setNewFiles(prev => [...prev, ...validFiles]);
    }
  }, [toast]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>, type: 'old' | 'new') => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (type === 'old') {
      setOldFiles(prev => [...prev, ...files]);
    } else {
      setNewFiles(prev => [...prev, ...files]);
    }
  };

  const removeFile = (index: number, type: 'old' | 'new') => {
    if (type === 'old') {
      setOldFiles(prev => prev.filter((_, i) => i !== index));
    } else {
      setNewFiles(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = () => {
    if (oldFiles.length === 0 || newFiles.length === 0) {
      toast({
        title: "خطأ",
        description: "يرجى رفع ملفات للمنهج القديم والجديد",
        variant: "destructive"
      });
      return;
    }

    if (oldFiles.length > 100 || newFiles.length > 100) {
      toast({
        title: "خطأ", 
        description: "لا يمكن رفع أكثر من 100 ملف لكل منهج",
        variant: "destructive"
      });
      return;
    }

    onFilesUploaded({ old: oldFiles, new: newFiles });
  };

  const DropZone = ({ type, files, title }: { type: 'old' | 'new', files: File[], title: string }) => (
    <Card className={`border-2 border-dashed transition-all duration-300 ${
      dragActive === type 
        ? 'border-blue-500 bg-blue-50 shadow-lg scale-105' 
        : 'border-gray-300 hover:border-gray-400'
    }`}>
      <CardHeader className="text-center pb-4">
        <CardTitle className="text-xl text-gray-800 flex items-center justify-center gap-2">
          <FolderOpen className="w-6 h-6" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={`min-h-48 flex flex-col items-center justify-center p-8 rounded-lg transition-colors ${
            dragActive === type ? 'bg-blue-100' : 'bg-gray-50'
          }`}
          onDragEnter={(e) => handleDrag(e, type)}
          onDragLeave={(e) => handleDrag(e, type)}
          onDragOver={(e) => handleDrag(e, type)}
          onDrop={(e) => handleDrop(e, type)}
        >
          <Upload className={`w-12 h-12 mb-4 ${dragActive === type ? 'text-blue-500' : 'text-gray-400'}`} />
          <p className="text-lg font-medium text-gray-700 mb-2">
            اسحب الملفات هنا أو انقر للتحديد
          </p>
          <p className="text-sm text-gray-500 mb-4">
            PDF, JPG, PNG (حتى 100 ملف)
          </p>
          
          <input
            type="file"
            multiple
            accept="image/*,.pdf"
            onChange={(e) => handleFileInput(e, type)}
            className="hidden"
            id={`file-input-${type}`}
          />
          <Button 
            variant="outline" 
            onClick={() => document.getElementById(`file-input-${type}`)?.click()}
            className="mb-4"
          >
            اختر الملفات
          </Button>

          {files.length > 0 && (
            <div className="w-full max-h-32 overflow-y-auto">
              <div className="space-y-2">
                {files.slice(0, 3).map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-white p-2 rounded shadow-sm">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-500" />
                      <span className="text-sm truncate max-w-40">{file.name}</span>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => removeFile(index, type)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ×
                    </Button>
                  </div>
                ))}
                {files.length > 3 && (
                  <div className="text-center text-sm text-gray-500 py-2">
                    و {files.length - 3} ملفات أخرى...
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {files.length > 0 && (
          <div className="mt-4 flex items-center justify-center gap-2 text-green-600">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium">{files.length} ملف جاهز للمعالجة</span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-6xl mx-auto">
      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <DropZone type="old" files={oldFiles} title="المنهج القديم" />
        <DropZone type="new" files={newFiles} title="المنهج الجديد" />
      </div>

      {/* إحصائيات سريعة */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="text-center p-4">
          <div className="text-2xl font-bold text-blue-600">{oldFiles.length}</div>
          <div className="text-sm text-gray-600">ملفات قديمة</div>
        </Card>
        <Card className="text-center p-4">
          <div className="text-2xl font-bold text-green-600">{newFiles.length}</div>
          <div className="text-sm text-gray-600">ملفات جديدة</div>
        </Card>
        <Card className="text-center p-4">
          <div className="text-2xl font-bold text-orange-600">
            {Math.max(oldFiles.length, newFiles.length) * 3}
          </div>
          <div className="text-sm text-gray-600">ثانية متوقعة</div>
        </Card>
        <Card className="text-center p-4">
          <div className="text-2xl font-bold text-purple-600">95%</div>
          <div className="text-sm text-gray-600">دقة متوقعة</div>
        </Card>
      </div>

      {/* تحذيرات ونصائح */}
      {(oldFiles.length > 50 || newFiles.length > 50) && (
        <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="flex items-center gap-2 text-orange-700">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">تحذير:</span>
          </div>
          <p className="text-orange-600 mt-1">
            عدد كبير من الملفات قد يؤثر على سرعة المعالجة. المدة المتوقعة: {Math.max(oldFiles.length, newFiles.length) * 3} ثانية
          </p>
        </div>
      )}

      <div className="text-center">
        <Button 
          onClick={handleSubmit}
          size="lg"
          className="px-12 py-4 text-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transform hover:scale-105 transition-all duration-200"
          disabled={oldFiles.length === 0 || newFiles.length === 0}
        >
          <Zap className="w-5 h-5 ml-2" />
          ابدأ المقارنة الذكية
        </Button>
        <p className="text-sm text-gray-500 mt-3">
          سيتم حفظ جميع البيانات محلياً لضمان الأمان والسرية
        </p>
      </div>
    </div>
  );
};

export default UploadSection;
