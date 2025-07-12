import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import difflib
from dataclasses import dataclass, asdict

from .multilingual_processor import MultilingualProcessor
from .gemini_service import GeminiService
from .batch_processor import BatchProcessor

@dataclass
class ComparisonConfig:
    """Configuration for comparison operations"""
    language_preference: Optional[str] = None
    enable_semantic_analysis: bool = True
    enable_structural_analysis: bool = True
    similarity_threshold: float = 0.7
    include_detailed_diff: bool = True
    max_context_length: int = 4000
    comparison_mode: str = 'comprehensive'  # 'fast', 'balanced', 'comprehensive'

@dataclass
class ComparisonResult:
    """Result of content comparison"""
    similarity_score: float
    primary_differences: List[str]
    detailed_analysis: Dict[str, Any]
    language_analysis: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    recommendations: List[str]

class EnhancedComparisonService:
    """Enhanced comparison service with multilingual support and optimized processing"""
    
    def __init__(self, config: Optional[ComparisonConfig] = None):
        self.config = config or ComparisonConfig()
        self.multilingual_processor = MultilingualProcessor()
        self.gemini_service = GeminiService()
        self.batch_processor = BatchProcessor()
    
    async def compare_content(self, 
                            old_content: str, 
                            new_content: str,
                            content_type: str = 'educational_material') -> ComparisonResult:
        """Enhanced content comparison with multilingual support"""
        
        start_time = datetime.now()
        
        # Process both contents with multilingual processor
        old_processed = self.multilingual_processor.process_multilingual_content(
            old_content, self.config.language_preference
        )
        new_processed = self.multilingual_processor.process_multilingual_content(
            new_content, self.config.language_preference
        )
        
        # Validate language consistency
        language_analysis = self._analyze_language_consistency(old_processed, new_processed)
        
        # Perform structural comparison
        structural_comparison = await self._perform_structural_comparison(
            old_processed, new_processed
        )
        
        # Perform semantic comparison using Gemini
        semantic_comparison = await self._perform_semantic_comparison(
            old_processed, new_processed, content_type, language_analysis
        )
        
        # Calculate overall similarity
        similarity_score = self._calculate_overall_similarity(
            structural_comparison, semantic_comparison
        )
        
        # Generate detailed analysis
        detailed_analysis = self._generate_detailed_analysis(
            old_processed, new_processed, structural_comparison, semantic_comparison
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            similarity_score, detailed_analysis, language_analysis
        )
        
        # Create processing metadata
        processing_time = (datetime.now() - start_time).total_seconds()
        processing_metadata = {
            'processing_time': processing_time,
            'comparison_mode': self.config.comparison_mode,
            'language_preference': self.config.language_preference,
            'old_content_stats': old_processed['processing_stats'],
            'new_content_stats': new_processed['processing_stats']
        }
        
        return ComparisonResult(
            similarity_score=similarity_score,
            primary_differences=self._extract_primary_differences(detailed_analysis),
            detailed_analysis=detailed_analysis,
            language_analysis=language_analysis,
            processing_metadata=processing_metadata,
            recommendations=recommendations
        )
    
    def _analyze_language_consistency(self, 
                                   old_processed: Dict[str, Any], 
                                   new_processed: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze language consistency between old and new content"""
        
        old_lang = old_processed['detected_language']
        new_lang = new_processed['detected_language']
        old_confidence = old_processed['confidence']
        new_confidence = new_processed['confidence']
        
        # Check for language mismatch
        language_mismatch = old_lang != new_lang
        confidence_drop = abs(old_confidence - new_confidence) > 0.3
        
        # Analyze content type consistency
        old_type = old_processed['metadata']['content_type']
        new_type = new_processed['metadata']['content_type']
        content_type_change = old_type != new_type
        
        return {
            'old_language': old_lang,
            'new_language': new_lang,
            'language_mismatch': language_mismatch,
            'confidence_drop': confidence_drop,
            'old_confidence': old_confidence,
            'new_confidence': new_confidence,
            'content_type_change': content_type_change,
            'old_content_type': old_type,
            'new_content_type': new_type,
            'language_consistency_score': self._calculate_language_consistency_score(
                old_lang, new_lang, old_confidence, new_confidence
            )
        }
    
    def _calculate_language_consistency_score(self, 
                                            old_lang: str, 
                                            new_lang: str, 
                                            old_conf: float, 
                                            new_conf: float) -> float:
        """Calculate language consistency score"""
        
        if old_lang == new_lang:
            # Same language, check confidence levels
            conf_score = 1.0 - abs(old_conf - new_conf) * 0.5
            return max(conf_score, 0.7)  # Minimum score for same language
        else:
            # Different languages, lower score
            avg_confidence = (old_conf + new_conf) / 2
            return avg_confidence * 0.5  # Penalize language mismatch
    
    async def _perform_structural_comparison(self, 
                                           old_processed: Dict[str, Any], 
                                           new_processed: Dict[str, Any]) -> Dict[str, Any]:
        """Perform structural comparison of content"""
        
        old_text = old_processed['processed_content']
        new_text = new_processed['processed_content']
        
        # Calculate basic similarity metrics
        sequence_matcher = difflib.SequenceMatcher(None, old_text, new_text)
        similarity_ratio = sequence_matcher.ratio()
        
        # Get detailed differences
        differences = list(sequence_matcher.get_opcodes())
        
        # Analyze content structure
        old_lines = old_text.split('\n')
        new_lines = new_text.split('\n')
        
        # Line-by-line comparison
        line_matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        line_similarity = line_matcher.ratio()
        
        # Word-level analysis
        old_words = old_text.split()
        new_words = new_text.split()
        
        word_matcher = difflib.SequenceMatcher(None, old_words, new_words)
        word_similarity = word_matcher.ratio()
        
        # Calculate structural metrics
        length_ratio = len(new_text) / len(old_text) if old_text else 0
        
        return {
            'character_similarity': similarity_ratio,
            'line_similarity': line_similarity,
            'word_similarity': word_similarity,
            'length_ratio': length_ratio,
            'differences': differences,
            'added_content': self._extract_added_content(differences, old_text, new_text),
            'removed_content': self._extract_removed_content(differences, old_text, new_text),
            'structural_score': (similarity_ratio + line_similarity + word_similarity) / 3
        }
    
    async def _perform_semantic_comparison(self, 
                                         old_processed: Dict[str, Any], 
                                         new_processed: Dict[str, Any],
                                         content_type: str,
                                         language_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform semantic comparison using Gemini AI"""
        
        # Prepare optimized content for Gemini analysis
        old_optimized = self._optimize_content_for_gemini(old_processed)
        new_optimized = self._optimize_content_for_gemini(new_processed)
        
        # Build context-aware prompt
        comparison_prompt = self._build_comparison_prompt(
            old_optimized, new_optimized, content_type, language_analysis
        )
        
        try:
            # Get Gemini analysis
            gemini_response = await self.gemini_service.analyze_comparison(
                comparison_prompt, language_analysis['old_language']
            )
            
            # Parse Gemini response
            semantic_analysis = self._parse_gemini_comparison_response(gemini_response)
            
            return semantic_analysis
            
        except Exception as e:
            # Fallback to basic semantic analysis
            return self._fallback_semantic_analysis(old_processed, new_processed)
    
    def _optimize_content_for_gemini(self, processed_content: Dict[str, Any]) -> str:
        """Optimize content for Gemini analysis by removing noise and focusing on key content"""
        
        content = processed_content['processed_content']
        metadata = processed_content['metadata']
        
        # If content is too long, summarize key points
        if len(content) > self.config.max_context_length:
            # Extract key sentences and important information
            sentences = content.split('. ')
            
            # Priority scoring for sentences
            scored_sentences = []
            for sentence in sentences:
                score = self._calculate_sentence_importance(sentence, metadata)
                scored_sentences.append((score, sentence))
            
            # Sort by importance and take top sentences
            scored_sentences.sort(reverse=True, key=lambda x: x[0])
            top_sentences = [sent[1] for sent in scored_sentences[:10]]  # Top 10 sentences
            
            optimized_content = '. '.join(top_sentences)
        else:
            optimized_content = content
        
        return optimized_content
    
    def _calculate_sentence_importance(self, sentence: str, metadata: Dict[str, Any]) -> float:
        """Calculate importance score for a sentence"""
        
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Educational content keywords (Arabic and English)
        educational_keywords = [
            'درس', 'فصل', 'وحدة', 'تمرين', 'سؤال', 'جواب', 'مثال', 'تعريف',
            'lesson', 'chapter', 'unit', 'exercise', 'question', 'answer', 'example', 'definition'
        ]
        
        # Mathematical keywords
        math_keywords = [
            'معادلة', 'حل', 'نتيجة', 'قانون', 'نظرية',
            'equation', 'solution', 'result', 'formula', 'theorem'
        ]
        
        # Count keyword matches
        for keyword in educational_keywords:
            if keyword in sentence_lower:
                score += 2.0
        
        for keyword in math_keywords:
            if keyword in sentence_lower:
                score += 1.5
        
        # Length bonus (moderate length preferred)
        length_score = min(len(sentence) / 100, 1.0)
        score += length_score
        
        # Number presence (often important in educational content)
        if any(char.isdigit() for char in sentence):
            score += 1.0
        
        return score
    
    def _build_comparison_prompt(self, 
                               old_content: str, 
                               new_content: str, 
                               content_type: str,
                               language_analysis: Dict[str, Any]) -> str:
        """Build optimized prompt for Gemini comparison"""
        
        language = language_analysis['old_language']
        
        if language == 'ar':
            prompt = f"""قم بمقارنة المحتوى التعليمي التالي وحدد الاختلافات الدلالية المهمة:

المحتوى الأصلي:
{old_content}

المحتوى الجديد:
{new_content}

يرجى التركيز على:
1. التغييرات في المعنى والمفاهيم الأساسية
2. إضافة أو حذف معلومات مهمة
3. تغييرات في الهيكل التعليمي
4. دقة المحتوى العلمي
5. وضوح الشرح والأمثلة

اعطني تحليلاً مفصلاً بتنسيق JSON يتضمن:
- درجة التشابه الدلالي (0-1)
- قائمة بالاختلافات المهمة
- تقييم جودة التحديث
- توصيات للتحسين"""
        else:
            prompt = f"""Compare the following educational content and identify important semantic differences:

Original Content:
{old_content}

New Content:
{new_content}

Please focus on:
1. Changes in meaning and core concepts
2. Addition or removal of important information
3. Changes in educational structure
4. Scientific content accuracy
5. Clarity of explanation and examples

Provide detailed analysis in JSON format including:
- Semantic similarity score (0-1)
- List of important differences
- Quality assessment of updates
- Improvement recommendations"""
        
        return prompt
    
    def _parse_gemini_comparison_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini's comparison response"""
        
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # If not JSON, create structured response from text
            return self._extract_analysis_from_text(response)
            
        except Exception:
            # Fallback parsing
            return {
                'semantic_similarity': 0.5,
                'key_differences': ['Unable to parse detailed analysis'],
                'quality_assessment': 'Analysis parsing failed',
                'recommendations': ['Review content manually']
            }
    
    def _extract_analysis_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured analysis from text response"""
        
        # Simple extraction logic - can be improved with more sophisticated NLP
        lines = text.split('\n')
        
        differences = []
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                if 'تحسين' in line or 'improve' in line.lower():
                    recommendations.append(line[1:].strip())
                else:
                    differences.append(line[1:].strip())
        
        return {
            'semantic_similarity': 0.7,  # Default moderate similarity
            'key_differences': differences[:5],  # Top 5 differences
            'quality_assessment': 'Parsed from text analysis',
            'recommendations': recommendations[:3]  # Top 3 recommendations
        }
    
    def _fallback_semantic_analysis(self, 
                                  old_processed: Dict[str, Any], 
                                  new_processed: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback semantic analysis when Gemini is unavailable"""
        
        old_words = set(old_processed['processed_content'].split())
        new_words = set(new_processed['processed_content'].split())
        
        # Calculate word overlap
        common_words = old_words.intersection(new_words)
        total_words = old_words.union(new_words)
        
        word_similarity = len(common_words) / len(total_words) if total_words else 0
        
        # Simple difference detection
        added_words = new_words - old_words
        removed_words = old_words - new_words
        
        return {
            'semantic_similarity': word_similarity,
            'key_differences': [
                f"Added content: {', '.join(list(added_words)[:5])}" if added_words else "",
                f"Removed content: {', '.join(list(removed_words)[:5])}" if removed_words else ""
            ],
            'quality_assessment': 'Basic word-level analysis',
            'recommendations': ['Consider detailed manual review']
        }
    
    def _calculate_overall_similarity(self, 
                                    structural: Dict[str, Any], 
                                    semantic: Dict[str, Any]) -> float:
        """Calculate overall similarity score combining structural and semantic analysis"""
        
        structural_weight = 0.4
        semantic_weight = 0.6
        
        structural_score = structural['structural_score']
        semantic_score = semantic['semantic_similarity']
        
        overall_score = (structural_score * structural_weight + 
                        semantic_score * semantic_weight)
        
        return round(overall_score, 3)
    
    def _generate_detailed_analysis(self, 
                                  old_processed: Dict[str, Any], 
                                  new_processed: Dict[str, Any],
                                  structural: Dict[str, Any], 
                                  semantic: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive detailed analysis"""
        
        return {
            'content_changes': {
                'length_change': len(new_processed['processed_content']) - len(old_processed['processed_content']),
                'length_change_percentage': ((len(new_processed['processed_content']) - len(old_processed['processed_content'])) / len(old_processed['processed_content']) * 100) if old_processed['processed_content'] else 0,
                'word_count_change': len(new_processed['processed_content'].split()) - len(old_processed['processed_content'].split()),
                'structural_similarity': structural['structural_score'],
                'semantic_similarity': semantic['semantic_similarity']
            },
            'quality_metrics': {
                'old_quality_score': old_processed['metadata']['quality_score'],
                'new_quality_score': new_processed['metadata']['quality_score'],
                'quality_improvement': new_processed['metadata']['quality_score'] - old_processed['metadata']['quality_score']
            },
            'content_analysis': {
                'old_content_type': old_processed['metadata']['content_type'],
                'new_content_type': new_processed['metadata']['content_type'],
                'arabic_ratio_change': new_processed['metadata']['content_analysis']['arabic_ratio'] - old_processed['metadata']['content_analysis']['arabic_ratio'],
                'english_ratio_change': new_processed['metadata']['content_analysis']['english_ratio'] - old_processed['metadata']['content_analysis']['english_ratio']
            },
            'key_differences': semantic.get('key_differences', []),
            'added_content': structural.get('added_content', []),
            'removed_content': structural.get('removed_content', [])
        }
    
    def _extract_primary_differences(self, detailed_analysis: Dict[str, Any]) -> List[str]:
        """Extract primary differences for summary"""
        
        differences = []
        
        # Length changes
        length_change = detailed_analysis['content_changes']['length_change_percentage']
        if abs(length_change) > 10:
            if length_change > 0:
                differences.append(f"المحتوى ازداد بنسبة {length_change:.1f}%")
            else:
                differences.append(f"المحتوى قل بنسبة {abs(length_change):.1f}%")
        
        # Quality changes
        quality_change = detailed_analysis['quality_metrics']['quality_improvement']
        if quality_change > 0.1:
            differences.append("تحسن في جودة المحتوى")
        elif quality_change < -0.1:
            differences.append("تراجع في جودة المحتوى")
        
        # Add semantic differences
        semantic_diffs = detailed_analysis.get('key_differences', [])
        differences.extend(semantic_diffs[:3])  # Top 3 semantic differences
        
        return differences[:5]  # Return top 5 differences
    
    def _generate_recommendations(self, 
                                similarity_score: float, 
                                detailed_analysis: Dict[str, Any], 
                                language_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results"""
        
        recommendations = []
        
        # Similarity-based recommendations
        if similarity_score < 0.3:
            recommendations.append("المحتوى مختلف جداً - يُنصح بمراجعة شاملة")
        elif similarity_score < 0.7:
            recommendations.append("تغييرات متوسطة - يُنصح بمراجعة التفاصيل")
        
        # Language consistency recommendations
        if language_analysis['language_mismatch']:
            recommendations.append("تم اكتشاف تغيير في لغة المحتوى - تحقق من الدقة")
        
        if language_analysis['confidence_drop']:
            recommendations.append("انخفض مستوى الثقة في اكتشاف اللغة - قد تحتاج لمراجعة إضافية")
        
        # Quality-based recommendations
        quality_change = detailed_analysis['quality_metrics']['quality_improvement']
        if quality_change < -0.1:
            recommendations.append("تراجعت جودة المحتوى - يُنصح بتحسين التنظيف والمعالجة")
        
        # Content type recommendations
        if detailed_analysis['content_analysis']['old_content_type'] != detailed_analysis['content_analysis']['new_content_type']:
            recommendations.append("تغير نوع المحتوى - تأكد من مناسبة المعالجة الجديدة")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _extract_added_content(self, differences: List, old_text: str, new_text: str) -> List[str]:
        """Extract added content from differences"""
        added = []
        for tag, i1, i2, j1, j2 in differences:
            if tag == 'insert':
                added_text = new_text[j1:j2].strip()
                if added_text and len(added_text) > 5:  # Ignore very short additions
                    added.append(added_text[:100])  # Limit length
        return added[:5]  # Top 5 additions
    
    def _extract_removed_content(self, differences: List, old_text: str, new_text: str) -> List[str]:
        """Extract removed content from differences"""
        removed = []
        for tag, i1, i2, j1, j2 in differences:
            if tag == 'delete':
                removed_text = old_text[i1:i2].strip()
                if removed_text and len(removed_text) > 5:  # Ignore very short deletions
                    removed.append(removed_text[:100])  # Limit length
        return removed[:5]  # Top 5 removals 