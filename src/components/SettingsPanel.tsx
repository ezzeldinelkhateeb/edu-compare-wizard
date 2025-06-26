
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Settings, 
  Globe, 
  Palette, 
  Zap, 
  Shield, 
  Download,
  Bell,
  Monitor
} from 'lucide-react';

const SettingsPanel: React.FC = () => {
  const [language, setLanguage] = useState<'ar' | 'en'>('ar');
  const [theme, setTheme] = useState<'light' | 'dark' | 'auto'>('light');
  const [notifications, setNotifications] = useState(true);
  const [autoSave, setAutoSave] = useState(true);
  const [processingQuality, setProcessingQuality] = useState([85]);
  const [maxFileSize, setMaxFileSize] = useState([50]);

  return (
    <div className="max-w-4xl mx-auto p-6" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-900">
          {language === 'ar' ? 'الإعدادات' : 'Settings'}
        </h1>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="general">
            {language === 'ar' ? 'عام' : 'General'}
          </TabsTrigger>
          <TabsTrigger value="processing">
            {language === 'ar' ? 'المعالجة' : 'Processing'}
          </TabsTrigger>
          <TabsTrigger value="appearance">
            {language === 'ar' ? 'المظهر' : 'Appearance'}
          </TabsTrigger>
          <TabsTrigger value="advanced">
            {language === 'ar' ? 'متقدم' : 'Advanced'}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5" />
                {language === 'ar' ? 'اللغة والمنطقة' : 'Language & Region'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">
                    {language === 'ar' ? 'لغة الواجهة' : 'Interface Language'}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {language === 'ar' 
                      ? 'اختر لغة الواجهة الرئيسية' 
                      : 'Choose the main interface language'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant={language === 'ar' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setLanguage('ar')}
                  >
                    العربية
                  </Button>
                  <Button 
                    variant={language === 'en' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setLanguage('en')}
                  >
                    English
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">
                    {language === 'ar' ? 'الإشعارات' : 'Notifications'}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {language === 'ar' 
                      ? 'تلقي إشعارات عند اكتمال المعالجة' 
                      : 'Receive notifications when processing is complete'}
                  </p>
                </div>
                <Switch 
                  checked={notifications}
                  onCheckedChange={setNotifications}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">
                    {language === 'ar' ? 'الحفظ التلقائي' : 'Auto Save'}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {language === 'ar' 
                      ? 'حفظ النتائج تلقائياً كل 5 دقائق' 
                      : 'Automatically save results every 5 minutes'}
                  </p>
                </div>
                <Switch 
                  checked={autoSave}
                  onCheckedChange={setAutoSave}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="processing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                {language === 'ar' ? 'إعدادات المعالجة' : 'Processing Settings'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium mb-2">
                  {language === 'ar' ? 'جودة المعالجة' : 'Processing Quality'}
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  {language === 'ar' 
                    ? 'أعلى = دقة أكبر ووقت أطول، أقل = معالجة أسرع' 
                    : 'Higher = Better accuracy & longer time, Lower = Faster processing'}
                </p>
                <div className="space-y-2">
                  <Slider
                    value={processingQuality}
                    onValueChange={setProcessingQuality}
                    max={100}
                    min={50}
                    step={5}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{language === 'ar' ? 'سريع' : 'Fast'}</span>
                    <span className="font-medium">{processingQuality[0]}%</span>
                    <span>{language === 'ar' ? 'دقيق' : 'Accurate'}</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">
                  {language === 'ar' ? 'الحد الأقصى لحجم الملف' : 'Maximum File Size'}
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  {language === 'ar' 
                    ? 'الحد الأقصى لحجم كل ملف بالميجابايت' 
                    : 'Maximum size per file in megabytes'}
                </p>
                <div className="space-y-2">
                  <Slider
                    value={maxFileSize}
                    onValueChange={setMaxFileSize}
                    max={200}
                    min={10}
                    step={10}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>10 MB</span>
                    <span className="font-medium">{maxFileSize[0]} MB</span>
                    <span>200 MB</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                {language === 'ar' ? 'المظهر والألوان' : 'Appearance & Colors'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-3">
                  {language === 'ar' ? 'المظهر' : 'Theme'}
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  <Button
                    variant={theme === 'light' ? 'default' : 'outline'}
                    onClick={() => setTheme('light')}
                    className="flex flex-col items-center gap-2 h-auto p-4"
                  >
                    <div className="w-6 h-6 bg-white border-2 border-gray-300 rounded"></div>
                    {language === 'ar' ? 'فاتح' : 'Light'}
                  </Button>
                  <Button
                    variant={theme === 'dark' ? 'default' : 'outline'}
                    onClick={() => setTheme('dark')}
                    className="flex flex-col items-center gap-2 h-auto p-4"
                  >
                    <div className="w-6 h-6 bg-gray-800 border-2 border-gray-600 rounded"></div>
                    {language === 'ar' ? 'داكن' : 'Dark'}
                  </Button>
                  <Button
                    variant={theme === 'auto' ? 'default' : 'outline'}
                    onClick={() => setTheme('auto')}
                    className="flex flex-col items-center gap-2 h-auto p-4"
                  >
                    <Monitor className="w-6 h-6" />
                    {language === 'ar' ? 'تلقائي' : 'Auto'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                {language === 'ar' ? 'الإعدادات المتقدمة' : 'Advanced Settings'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  {language === 'ar' 
                    ? 'تحذير: تغيير هذه الإعدادات قد يؤثر على أداء النظام' 
                    : 'Warning: Changing these settings may affect system performance'}
                </p>
              </div>

              <div className="space-y-4">
                <Button variant="outline" className="w-full">
                  <Download className="w-4 h-4 mr-2" />
                  {language === 'ar' ? 'تصدير الإعدادات' : 'Export Settings'}
                </Button>
                
                <Button variant="outline" className="w-full">
                  <Bell className="w-4 h-4 mr-2" />
                  {language === 'ar' ? 'مسح ذاكرة التخزين المؤقت' : 'Clear Cache'}
                </Button>

                <Button variant="destructive" className="w-full">
                  {language === 'ar' ? 'إعادة تعيين جميع الإعدادات' : 'Reset All Settings'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          {language === 'ar' 
            ? 'سيتم حفظ الإعدادات تلقائياً عند التغيير' 
            : 'Settings are automatically saved when changed'}
        </p>
      </div>
    </div>
  );
};

export default SettingsPanel;
