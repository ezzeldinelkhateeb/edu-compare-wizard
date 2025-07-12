import re
import json
from typing import Dict, List, Optional, Tuple, Any
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import unicodedata
from dataclasses import dataclass

@dataclass
class LanguageConfig:
    """Configuration for language-specific processing"""
    name: str
    code: str
    rtl: bool = False
    confidence_threshold: float = 0.6
    cleaning_patterns: List[str] = None
    preserve_patterns: List[str] = None

class MultilingualProcessor:
    """Enhanced multilingual content processor with automatic language detection"""
    
    def __init__(self):
        self.supported_languages = {
            'ar': LanguageConfig(
                name='Arabic',
                code='ar',
                rtl=True,
                confidence_threshold=0.6,
                cleaning_patterns=[
                    r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\d\w\-\.\,\!\?\:\;\(\)]',
                    r'\s+',  # Multiple spaces
                ],
                preserve_patterns=[
                    r'[\u0600-\u06FF]+',  # Arabic text
                    r'\d+',  # Numbers
                    r'[A-Za-z]+',  # English words that might be mixed in
                ]
            ),
            'en': LanguageConfig(
                name='English',
                code='en',
                rtl=False,
                confidence_threshold=0.6,
                cleaning_patterns=[
                    r'[^\w\s\-\.\,\!\?\:\;\(\)\[\]\{\}\"\'\/\\]',
                    r'\s+',  # Multiple spaces
                ],
                preserve_patterns=[
                    r'[A-Za-z]+',  # English words
                    r'\d+',  # Numbers
                    r'[\u0600-\u06FF]+',  # Arabic text that might be mixed in
                ]
            )
        }
        
    def detect_content_language(self, text: str) -> Tuple[str, float]:
        """Detect the primary language of the content with confidence score"""
        if not text or len(text.strip()) < 10:
            return 'unknown', 0.0
            
        try:
            # Clean text for better detection
            cleaned_text = self._prepare_text_for_detection(text)
            
            # Use multiple detection attempts
            detections = detect_langs(cleaned_text)
            
            # Find the most confident supported language
            for detection in detections:
                if detection.lang in self.supported_languages:
                    return detection.lang, detection.prob
                    
            # Fallback to simple character-based detection
            return self._character_based_detection(text)
            
        except LangDetectException:
            return self._character_based_detection(text)
    
    def _prepare_text_for_detection(self, text: str) -> str:
        """Prepare text for language detection by removing noise"""
        # Remove URLs, emails, and special formatting
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _character_based_detection(self, text: str) -> Tuple[str, float]:
        """Fallback character-based language detection"""
        total_chars = len(text)
        if total_chars == 0:
            return 'unknown', 0.0
            
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[A-Za-z]', text))
        
        arabic_ratio = arabic_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if arabic_ratio > 0.3:
            return 'ar', min(arabic_ratio * 2, 1.0)
        elif english_ratio > 0.3:
            return 'en', min(english_ratio * 2, 1.0)
        else:
            return 'unknown', 0.0
    
    def process_multilingual_content(self, 
                                   content: str, 
                                   user_selected_language: Optional[str] = None,
                                   preserve_mixed_content: bool = True) -> Dict[str, Any]:
        """Process content with multilingual support"""
        
        # Detect language if not provided by user
        if user_selected_language:
            detected_lang = user_selected_language
            confidence = 1.0  # User selection has highest confidence
        else:
            detected_lang, confidence = self.detect_content_language(content)
        
        # Get language configuration
        lang_config = self.supported_languages.get(detected_lang)
        if not lang_config:
            # Default to English if language not supported
            lang_config = self.supported_languages['en']
            detected_lang = 'en'
        
        # Process content based on detected language
        processed_content = self._apply_language_specific_cleaning(
            content, lang_config, preserve_mixed_content
        )
        
        # Extract metadata
        metadata = self._extract_content_metadata(content, processed_content, lang_config)
        
        return {
            'original_content': content,
            'processed_content': processed_content,
            'detected_language': detected_lang,
            'confidence': confidence,
            'language_config': {
                'name': lang_config.name,
                'code': lang_config.code,
                'rtl': lang_config.rtl
            },
            'metadata': metadata,
            'processing_stats': {
                'original_length': len(content),
                'processed_length': len(processed_content),
                'reduction_percentage': ((len(content) - len(processed_content)) / len(content) * 100) if content else 0
            }
        }
    
    def _apply_language_specific_cleaning(self, 
                                        content: str, 
                                        lang_config: LanguageConfig,
                                        preserve_mixed: bool) -> str:
        """Apply language-specific cleaning rules"""
        
        if not content:
            return ""
        
        # Start with the original content
        cleaned = content
        
        # Apply preserve patterns first if preserving mixed content
        if preserve_mixed and lang_config.preserve_patterns:
            preserved_parts = []
            for pattern in lang_config.preserve_patterns:
                matches = re.findall(pattern, cleaned)
                preserved_parts.extend(matches)
        
        # Apply cleaning patterns
        if lang_config.cleaning_patterns:
            for pattern in lang_config.cleaning_patterns:
                if pattern == r'\s+':
                    # Handle multiple spaces specially
                    cleaned = re.sub(pattern, ' ', cleaned)
                else:
                    cleaned = re.sub(pattern, ' ', cleaned)
        
        # Clean up whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _extract_content_metadata(self, 
                                original: str, 
                                processed: str, 
                                lang_config: LanguageConfig) -> Dict[str, Any]:
        """Extract metadata about the content processing"""
        
        # Count different types of content
        arabic_words = len(re.findall(r'[\u0600-\u06FF]+', processed))
        english_words = len(re.findall(r'[A-Za-z]+', processed))
        numbers = len(re.findall(r'\d+', processed))
        
        # Calculate ratios
        total_elements = arabic_words + english_words + numbers
        
        return {
            'content_analysis': {
                'arabic_words': arabic_words,
                'english_words': english_words,
                'numbers': numbers,
                'total_elements': total_elements,
                'arabic_ratio': arabic_words / total_elements if total_elements > 0 else 0,
                'english_ratio': english_words / total_elements if total_elements > 0 else 0
            },
            'content_type': self._determine_content_type(arabic_words, english_words, numbers),
            'quality_score': self._calculate_quality_score(original, processed)
        }
    
    def _determine_content_type(self, arabic_words: int, english_words: int, numbers: int) -> str:
        """Determine the type of content based on word analysis"""
        total = arabic_words + english_words + numbers
        
        if total == 0:
            return 'empty'
        
        arabic_ratio = arabic_words / total
        english_ratio = english_words / total
        
        if arabic_ratio > 0.7:
            return 'primarily_arabic'
        elif english_ratio > 0.7:
            return 'primarily_english'
        elif arabic_ratio > 0.3 and english_ratio > 0.3:
            return 'bilingual'
        else:
            return 'mixed_content'
    
    def _calculate_quality_score(self, original: str, processed: str) -> float:
        """Calculate a quality score for the processed content"""
        if not original:
            return 0.0
        
        # Base score on content preservation
        length_ratio = len(processed) / len(original)
        
        # Penalize too much reduction or too little reduction
        if length_ratio < 0.1:  # Too much removed
            return 0.2
        elif length_ratio > 0.95:  # Too little cleaning
            return 0.5
        else:
            # Optimal range is 0.3-0.8
            if 0.3 <= length_ratio <= 0.8:
                return 0.9
            else:
                return 0.7
    
    def process_landing_ai_content(self, 
                                 landing_ai_result: Dict[str, Any],
                                 user_language: Optional[str] = None) -> Dict[str, Any]:
        """Process Landing AI results with improved filtering"""
        
        extracted_text = landing_ai_result.get('extracted_text', '')
        image_descriptions = landing_ai_result.get('image_descriptions', [])
        
        # Process main text
        text_result = self.process_multilingual_content(
            extracted_text, 
            user_language, 
            preserve_mixed_content=True
        )
        
        # Process and filter image descriptions
        filtered_descriptions = []
        for desc in image_descriptions:
            if self._is_relevant_description(desc, text_result['detected_language']):
                desc_result = self.process_multilingual_content(
                    desc, 
                    user_language, 
                    preserve_mixed_content=True
                )
                filtered_descriptions.append({
                    'original': desc,
                    'processed': desc_result['processed_content'],
                    'relevance_score': self._calculate_relevance_score(desc, extracted_text)
                })
        
        return {
            'processed_text': text_result,
            'filtered_descriptions': filtered_descriptions,
            'summary': {
                'total_descriptions': len(image_descriptions),
                'relevant_descriptions': len(filtered_descriptions),
                'filter_efficiency': len(filtered_descriptions) / len(image_descriptions) if image_descriptions else 0
            }
        }
    
    def _is_relevant_description(self, description: str, detected_language: str) -> bool:
        """Determine if an image description is relevant for content analysis"""
        
        # Skip very generic descriptions
        generic_terms = [
            'image', 'picture', 'photo', 'diagram', 'chart', 'table',
            'صورة', 'رسم', 'جدول', 'مخطط'
        ]
        
        desc_lower = description.lower()
        if any(term in desc_lower for term in generic_terms) and len(description) < 50:
            return False
        
        # Keep descriptions that contain educational content markers
        educational_markers = [
            'lesson', 'chapter', 'exercise', 'question', 'answer', 'formula',
            'درس', 'فصل', 'تمرين', 'سؤال', 'جواب', 'معادلة'
        ]
        
        if any(marker in desc_lower for marker in educational_markers):
            return True
        
        # Keep if it contains substantial text (likely OCR content)
        if len(description) > 100:
            return True
        
        return False
    
    def _calculate_relevance_score(self, description: str, main_text: str) -> float:
        """Calculate how relevant an image description is to the main content"""
        
        if not main_text or not description:
            return 0.0
        
        # Simple keyword overlap scoring
        desc_words = set(description.lower().split())
        text_words = set(main_text.lower().split())
        
        overlap = len(desc_words.intersection(text_words))
        total_desc_words = len(desc_words)
        
        if total_desc_words == 0:
            return 0.0
        
        return min(overlap / total_desc_words, 1.0) 