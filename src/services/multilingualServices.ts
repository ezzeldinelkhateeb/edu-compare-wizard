// خدمات دعم اللغات المتعددة
export const multilingualServices = {
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 بايت';
    const k = 1024;
    const sizes = ['بايت', 'ك.ب', 'م.ب', 'ج.ب'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
  
  getLanguageDisplayName: (code: string): string => {
    const languages: Record<string, string> = {
      ar: 'العربية',
      en: 'English',
      auto: 'اكتشاف تلقائي',
      fr: 'Français',
      es: 'Español',
      de: 'Deutsch'
    };
    return languages[code] || code;
  }
};

export default multilingualServices; 