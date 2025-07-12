import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Globe, Languages, Check } from 'lucide-react';

export interface LanguageOption {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'auto', name: 'Auto Detect', nativeName: 'اكتشاف تلقائي', flag: '🌐' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳' },
  { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷' },
  { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', flag: '🇳🇱' },
];

export interface LanguageDetection {
  language: string;
  confidence: number;
  detectedAt: Date;
}

export interface LanguageSelectorProps {
  selectedLanguage: string;
  onLanguageChange: (language: string) => void;
  showDetectionStatus?: boolean;
  detectedLanguage?: string;
  confidence?: number;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function LanguageSelector({
  selectedLanguage,
  onLanguageChange,
  showDetectionStatus = false,
  detectedLanguage,
  confidence,
  disabled = false,
  size = 'md'
}: LanguageSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const getLanguageInfo = (code: string): LanguageOption => {
    return SUPPORTED_LANGUAGES.find(lang => lang.code === code) || SUPPORTED_LANGUAGES[0];
  };

  const selectedInfo = getLanguageInfo(selectedLanguage);
  const detectedInfo = detectedLanguage ? getLanguageInfo(detectedLanguage) : null;

  const handleLanguageSelect = (language: string) => {
    onLanguageChange(language);
    setIsOpen(false);
  };

  const sizeClasses = {
    sm: 'text-sm p-2',
    md: 'text-base p-3',
    lg: 'text-lg p-4'
  };

  return (
    <div className="space-y-3">
      {/* Language Selector */}
      <div className="relative">
        <Button
          variant="outline"
          onClick={() => setIsOpen(!isOpen)}
          disabled={disabled}
          className={`w-full justify-between ${sizeClasses[size]}`}
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">{selectedInfo.flag}</span>
            <span className="font-medium">{selectedInfo.nativeName}</span>
            <span className="text-sm text-muted-foreground">({selectedInfo.name})</span>
          </div>
          <Languages className="h-4 w-4" />
        </Button>

        {isOpen && (
          <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {SUPPORTED_LANGUAGES.map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageSelect(language.code)}
                className={`w-full text-left px-3 py-2 hover:bg-gray-50 flex items-center justify-between
                  ${selectedLanguage === language.code ? 'bg-blue-50 text-blue-700' : ''}`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{language.flag}</span>
                  <div>
                    <div className="font-medium">{language.nativeName}</div>
                    <div className="text-sm text-muted-foreground">{language.name}</div>
                  </div>
                </div>
                {selectedLanguage === language.code && (
                  <Check className="h-4 w-4 text-blue-700" />
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detection Status */}
      {showDetectionStatus && detectedInfo && confidence && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 text-sm">
              <Globe className="h-4 w-4 text-blue-600" />
              <span className="font-medium text-blue-800">تم اكتشاف اللغة:</span>
              <Badge variant="outline" className="bg-white">
                {detectedInfo.flag} {detectedInfo.nativeName}
              </Badge>
              <span className="text-blue-600">({Math.round(confidence * 100)}% ثقة)</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Hook for managing language selection and detection
export function useLanguageSelection() {
  const [selectedLanguage, setSelectedLanguage] = useState<string>('auto');
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number>(0);
  const [detectionHistory, setDetectionHistory] = useState<LanguageDetection[]>([]);

  const updateDetection = (language: string, confidenceLevel: number) => {
    setDetectedLanguage(language);
    setConfidence(confidenceLevel);
    
    // Add to history
    setDetectionHistory(prev => [
      {
        language,
        confidence: confidenceLevel,
        detectedAt: new Date()
      },
      ...prev.slice(0, 9) // Keep last 10 detections
    ]);
  };

  const resetDetection = () => {
    setDetectedLanguage(null);
    setConfidence(0);
  };

  const getLanguageDisplayName = (code: string): string => {
    const info = SUPPORTED_LANGUAGES.find(lang => lang.code === code);
    return info ? info.nativeName : code;
  };

  const isAutoDetectMode = () => selectedLanguage === 'auto';

  return {
    selectedLanguage,
    setSelectedLanguage,
    detectedLanguage,
    confidence,
    detectionHistory,
    updateDetection,
    resetDetection,
    getLanguageDisplayName,
    isAutoDetectMode
  };
} 