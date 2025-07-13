import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, FileText, BarChart3, Download, BookOpen, Zap, Shield, Globe, Brain, Rocket } from 'lucide-react';
import UploadSection, { ProcessingSettings } from '@/components/UploadSection';
import SmartComparisonDashboard from '@/components/SmartComparisonDashboard';
import GeminiConnectionTest from '@/components/GeminiConnectionTest';
import { useToast } from '@/hooks/use-toast';

const Index = () => {
  const [currentStep, setCurrentStep] = useState<'upload' | 'smart'>('upload');
  const [uploadedFiles, setUploadedFiles] = useState<{old: File[], new: File[]} | null>(null);
  const [processingSettings, setProcessingSettings] = useState<ProcessingSettings | null>(null);
  const { toast } = useToast();

  const handleFilesUploaded = (files: {old: File[], new: File[]}, settings: ProcessingSettings) => {
    console.log('📁 تم رفع الملفات:', {
      oldFiles: files.old.map(f => f.name),
      newFiles: files.new.map(f => f.name),
      settings: settings
    });
    
    setUploadedFiles(files);
    setProcessingSettings(settings);
    setCurrentStep('smart');
    
    toast({
      title: "تم رفع الملفات",
      description: `جاري بدء المقارنة باستخدام ${settings.processingMode === 'gemini_only' ? 'Gemini فقط' : 'LandingAI + Gemini'}...`,
      duration: 3000
    });
  };

  const features = [
    {
      icon: Brain,
      title: "نظام ذكي متدرج",
      description: "3 مراحل ذكية توفر 35-50% من التكاليف",
      isNew: true
    },
    {
      icon: Zap,
      title: "مقارنة بصرية فورية",
      description: "كشف التطابق الكامل بدون تكلفة إضافية",
      isNew: true
    },
    {
      icon: Globe,
      title: "دعم متعدد اللغات", 
      description: "واجهة عربية/إنجليزية مع دعم كامل لـ RTL"
    },
    {
      icon: Shield,
      title: "أمان عالي",
      description: "حماية البيانات التعليمية بأعلى معايير الأمان"
    },
    {
      icon: BarChart3,
      title: "تقارير تفاعلية",
      description: "تقارير مرئية شاملة وقابلة للتصدير"
    },
    {
      icon: FileText,
      title: "تحليل عميق بالذكاء الاصطناعي",
      description: "Gemini AI لتحليل التغييرات والتوصيات",
      isNew: true
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50" dir="rtl">
      {/* الهيدر */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl text-white">
                <BookOpen className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  مقارن المناهج التعليمية
                </h1>
                <p className="text-sm text-gray-600">نظام ذكي لمقارنة المناهج الدراسية</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">English</Button>
              <Button variant="ghost" size="sm">تسجيل الدخول</Button>
            </div>
          </div>
        </div>
      </header>

      {currentStep === 'upload' && (
        <>
          {/* القسم الرئيسي */}
          <section className="container mx-auto px-6 py-16">
            <div className="text-center max-w-4xl mx-auto mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                النظام الذكي لمقارنة المناهج التعليمية
              </h2>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                نظام ذكي متدرج يوفر 35-50% من التكاليف مع دقة 100% في المقارنة البصرية
                <br />
                معالجة سريعة ومتوازية مع تقارير تفصيلية احترافية
              </p>
              
              <div className="flex flex-wrap justify-center gap-4 mb-12">
                <div className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-full">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">دقة 100% في المقارنة البصرية</span>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-700 rounded-full">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">توفير 35-50% في التكلفة</span>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-full">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">معالجة 7+ ملفات/ثانية</span>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-orange-50 text-orange-700 rounded-full">
                  <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">تحليل ذكي بـ Gemini AI</span>
                </div>
              </div>
            </div>

            <UploadSection onFilesUploaded={handleFilesUploaded} />
          </section>

          {/* قسم الميزات */}
          <section className="bg-white py-20">
            <div className="container mx-auto px-6">
              <div className="text-center mb-16">
                <h3 className="text-3xl font-bold text-gray-900 mb-4">
                  لماذا تختار نظامنا؟
                </h3>
                <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                  نحن نقدم حلولاً متطورة تعتمد على أحدث تقنيات الذكاء الاصطناعي
                </p>
              </div>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {features.map((feature, index) => (
                  <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 relative">
                    <CardContent className="p-8 text-center">
                      {feature.isNew && (
                        <div className="absolute -top-2 -right-2 bg-gradient-to-r from-orange-500 to-red-500 text-white text-xs px-3 py-1 rounded-full font-bold">
                          جديد
                        </div>
                      )}
                      <div className={`w-16 h-16 ${
                        feature.isNew 
                          ? 'bg-gradient-to-br from-purple-500 to-blue-600' 
                          : 'bg-gradient-to-br from-blue-500 to-indigo-600'
                      } rounded-2xl flex items-center justify-center mx-auto mb-6`}>
                        <feature.icon className="w-8 h-8 text-white" />
                      </div>
                      <h4 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h4>
                      <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </section>

          {/* قسم اختبار الاتصال */}
          <section className="bg-gradient-to-br from-green-50 to-blue-50 py-16">
            <div className="container mx-auto px-6">
              <div className="text-center mb-12">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">
                  اختبار الاتصال
                </h3>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  تحقق من حالة الاتصال بالخادم وخدمات الذكاء الاصطناعي
                </p>
              </div>
              
              <div className="flex justify-center">
                <GeminiConnectionTest />
              </div>
            </div>
          </section>

          {/* قسم كيف يعمل */}
          <section className="bg-gradient-to-br from-gray-50 to-blue-50 py-20">
            <div className="container mx-auto px-6">
              <div className="text-center mb-16">
                <h3 className="text-3xl font-bold text-gray-900 mb-4">
                  كيف يعمل النظام؟
                </h3>
                <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                  عملية بسيطة في 3 خطوات للحصول على نتائج احترافية
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
                {[
                  { step: 1, icon: Upload, title: "ارفع الملفات", desc: "قم برفع المجلدين القديم والجديد" },
                  { step: 2, icon: Zap, title: "المعالجة الذكية", desc: "تحليل بصري ونصي متطور بالذكاء الاصطناعي" },
                  { step: 3, icon: Download, title: "احصل على التقرير", desc: "تقرير تفاعلي وملف PowerPoint جاهز" }
                ].map((item, index) => (
                  <div key={index} className="text-center relative">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6 relative">
                      <item.icon className="w-10 h-10 text-white" />
                      <div className="absolute -top-2 -right-2 w-8 h-8 bg-orange-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        {item.step}
                      </div>
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">{item.title}</h4>
                    <p className="text-gray-600">{item.desc}</p>
                    {index < 2 && (
                      <div className="hidden md:block absolute top-10 left-1/2 transform translate-x-8 w-16 h-0.5 bg-gradient-to-r from-blue-300 to-indigo-300"></div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>
        </>
      )}

      {currentStep === 'smart' && (
        <SmartComparisonDashboard 
          files={uploadedFiles}
          processingSettings={processingSettings}
          onBack={() => setCurrentStep('upload')} 
        />
      )}

      {/* الفوتر */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl">
                  <BookOpen className="w-6 h-6" />
                </div>
                <h4 className="text-xl font-bold">مقارن المناهج</h4>
              </div>
              <p className="text-gray-400">
                نظام ذكي لمقارنة المناهج التعليمية باستخدام أحدث تقنيات الذكاء الاصطناعي
              </p>
            </div>
            <div>
              <h5 className="font-bold mb-4">المنتج</h5>
              <ul className="space-y-2 text-gray-400">
                <li>الميزات</li>
                <li>التسعير</li>
                <li>التوثيق</li>
                <li>الدعم</li>
              </ul>
            </div>
            <div>
              <h5 className="font-bold mb-4">الشركة</h5>
              <ul className="space-y-2 text-gray-400">
                <li>حولنا</li>
                <li>فريق العمل</li>
                <li>اتصل بنا</li>
                <li>الأخبار</li>
              </ul>
            </div>
            <div>
              <h5 className="font-bold mb-4">المساعدة</h5>
              <ul className="space-y-2 text-gray-400">
                <li>مركز المساعدة</li>
                <li>الأسئلة الشائعة</li>
                <li>سياسة الخصوصية</li>
                <li>شروط الاستخدام</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 مقارن المناهج التعليمية. جميع الحقوق محفوظة.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
