"""
نماذج البيانات للـ API
Pydantic Models for API Request/Response
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """حالات الوظائف"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileType(str, Enum):
    """أنواع الملفات"""
    OLD = "old"
    NEW = "new"


class ProcessingStage(str, Enum):
    """مراحل المعالجة"""
    INITIALIZATION = "initialization"
    UPLOAD = "upload"
    OCR_EXTRACTION = "ocr_extraction"
    VISUAL_ANALYSIS = "visual_analysis"
    TEXT_COMPARISON = "text_comparison"
    REPORT_GENERATION = "report_generation"


# نماذج الرفع
class FileUploadResponse(BaseModel):
    """استجابة رفع الملف"""
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    upload_url: str
    message: str = "تم رفع الملف بنجاح"


class UploadSessionRequest(BaseModel):
    """طلب إنشاء جلسة رفع جديدة"""
    session_name: Optional[str] = Field(None, description="اسم الجلسة")
    description: Optional[str] = Field(None, description="وصف الجلسة")
    

class UploadSessionResponse(BaseModel):
    """استجابة إنشاء جلسة رفع"""
    session_id: str
    session_name: str
    created_at: datetime
    status: JobStatus
    message: str = "تم إنشاء الجلسة بنجاح"


# نماذج المعالجة
class ProcessingProgress(BaseModel):
    """تقدم المعالجة"""
    job_id: str
    session_id: str
    status: JobStatus
    current_stage: ProcessingStage
    progress_percentage: float = Field(..., ge=0, le=100)
    current_file: Optional[str] = None
    files_processed: int = 0
    total_files: int = 0
    estimated_time_remaining: Optional[int] = Field(None, description="الوقت المتبقي بالثواني")
    message: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StartComparisonRequest(BaseModel):
    """طلب بدء المقارنة"""
    session_id: str
    old_files: List[str] = Field(..., description="معرفات الملفات القديمة")
    new_files: List[str] = Field(..., description="معرفات الملفات الجديدة")
    comparison_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class StartComparisonResponse(BaseModel):
    """استجابة بدء المقارنة"""
    job_id: str
    session_id: str
    status: JobStatus
    message: str = "تم بدء عملية المقارنة"


# نماذج النتائج
class AIExtractionResult(BaseModel):
    """نتائج استخراج الذكاء الاصطناعي"""
    extracted_text: str
    confidence_score: float = Field(..., ge=0, le=1)
    structured_data: Optional[Dict[str, Any]] = None
    processing_time: float = Field(..., description="وقت المعالجة بالثواني")
    service_used: str = Field(..., description="الخدمة المستخدمة (LandingAI, etc.)")


class VisualComparisonResult(BaseModel):
    """نتائج المقارنة البصرية"""
    similarity_score: float = Field(..., ge=0, le=100)
    ssim_score: float = Field(..., ge=0, le=1)
    phash_score: float = Field(..., ge=0, le=1)
    clip_score: Optional[float] = Field(None, ge=0, le=1)
    difference_map_url: Optional[str] = None
    processing_time: float


class TextComparisonResult(BaseModel):
    """نتائج مقارنة النصوص"""
    similarity_percentage: float = Field(..., ge=0, le=100)
    content_changes: List[str] = Field(default_factory=list)
    questions_changes: List[str] = Field(default_factory=list)
    examples_changes: List[str] = Field(default_factory=list)
    major_differences: List[str] = Field(default_factory=list)
    summary: str
    recommendation: str
    processing_time: float
    service_used: str = "Gemini"


class FileComparisonResult(BaseModel):
    """نتيجة مقارنة ملف واحد"""
    file_pair_id: str
    old_file_name: str
    new_file_name: str
    old_file_url: str
    new_file_url: str
    
    # نتائج الاستخراج
    old_extraction: AIExtractionResult
    new_extraction: AIExtractionResult
    
    # نتائج المقارنة
    visual_comparison: VisualComparisonResult
    text_comparison: TextComparisonResult
    
    # النتيجة الإجمالية
    overall_similarity: float = Field(..., ge=0, le=100)
    status: str
    processing_time: float
    created_at: datetime


class ComparisonSessionResult(BaseModel):
    """نتائج جلسة المقارنة الكاملة"""
    session_id: str
    job_id: str
    session_name: str
    status: JobStatus
    
    # إحصائيات عامة
    total_files: int
    processed_files: int
    identical_files: int = 0
    changed_files: int = 0
    failed_files: int = 0
    
    # متوسطات
    average_visual_similarity: float = 0
    average_text_similarity: float = 0
    average_overall_similarity: float = 0
    
    # النتائج التفصيلية
    file_results: List[FileComparisonResult] = Field(default_factory=list)
    
    # أوقات المعالجة
    total_processing_time: float = 0
    created_at: datetime
    completed_at: Optional[datetime] = None


# نماذج التصدير
class ExportFormat(str, Enum):
    """صيغ التصدير"""
    HTML = "html"
    PDF = "pdf"
    PPTX = "pptx"
    JSON = "json"
    MARKDOWN = "markdown"


class ExportRequest(BaseModel):
    """طلب تصدير التقرير"""
    session_id: str
    format: ExportFormat
    include_images: bool = True
    include_detailed_analysis: bool = True
    language: str = Field(default="ar", pattern="^(ar|en)$")


class ExportResponse(BaseModel):
    """استجابة التصدير"""
    export_id: str
    session_id: str
    format: ExportFormat
    download_url: str
    file_size: int
    expires_at: datetime
    message: str = "تم إنشاء التقرير بنجاح"


# نماذج الأخطاء
class ErrorResponse(BaseModel):
    """استجابة الخطأ"""
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseModel):
    """استجابة النجاح العامة"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# نماذج WebSocket
class WebSocketMessage(BaseModel):
    """رسالة WebSocket"""
    type: str = Field(..., description="نوع الرسالة")
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ProgressUpdate(WebSocketMessage):
    """تحديث التقدم عبر WebSocket"""
    type: str = "progress_update"
    job_id: str
    progress: ProcessingProgress 


class ProcessingSessionRequest(BaseModel):
    """طلب إنشاء جلسة معالجة"""
    session_name: Optional[str] = None
    description: Optional[str] = None


class ProcessingSessionResponse(BaseModel):
    """استجابة إنشاء جلسة معالجة"""
    session_id: str
    status: str
    message: str


class ProcessingStep(BaseModel):
    """خطوة معالجة"""
    id: str
    name: str
    status: str = "pending"  # pending, processing, completed, error
    progress: int = 0
    duration: Optional[float] = None
    confidence: Optional[float] = None
    details: Optional[str] = None
    attempts: Optional[int] = None
    max_attempts: Optional[int] = None


class OCRAttempt(BaseModel):
    """محاولة OCR"""
    language: str
    config: str
    confidence: float
    success: bool
    duration: float
    text_length: int


class ProcessingResult(BaseModel):
    """نتيجة معالجة ملف"""
    id: str
    filename: str
    status: str = "pending"  # pending, processing, completed, error
    confidence: float = 0.0
    text_length: int = 0
    word_count: int = 0
    processing_time: float = 0.0
    language: str = "unknown"
    ocr_attempts: List[OCRAttempt] = []
    extracted_text: str = ""
    markdown_content: str = ""
    structured_analysis: Optional[Dict[str, Any]] = None


class ComparisonResult(BaseModel):
    """نتيجة المقارنة"""
    id: str
    old_file_id: str
    new_file_id: str
    similarity: float = 0.0
    confidence: float = 0.0
    processing_time: float = 0.0
    changes: List[str] = []
    summary: str = ""
    recommendation: str = ""
    detailed_analysis: str = ""
    status: str = "pending"  # pending, processing, completed, error


class AdvancedProcessingStatus(BaseModel):
    """حالة المعالجة المتقدمة"""
    session_id: str
    status: str
    progress: float
    current_step: str
    processing_steps: List[ProcessingStep]
    old_files_count: int
    new_files_count: int
    processing_results_count: int
    comparison_results_count: int
    logs: List[str]
    created_at: str
    updated_at: str


class AdvancedProcessingResults(BaseModel):
    """نتائج المعالجة المتقدمة الكاملة"""
    session_id: str
    status: str
    processing_results: List[ProcessingResult]
    comparison_results: List[ComparisonResult]
    statistics: Dict[str, Any]
    logs: List[str]

# Ultra Fast Comparison Schemas
class UltraFastComparisonRequest(BaseModel):
    """طلب المقارنة السريعة"""
    session_name: Optional[str] = Field(None, description="اسم الجلسة")
    old_image_path: str = Field(..., description="مسار الصورة القديمة")
    new_image_path: str = Field(..., description="مسار الصورة الجديدة")

class UltraFastComparisonResponse(BaseModel):
    """استجابة المقارنة السريعة"""
    session_id: str
    status: JobStatus
    message: str = "تم بدء المقارنة السريعة"
    
class ComparisonResponse(BaseModel):
    """استجابة عامة للمقارنة"""
    session_id: str
    job_id: Optional[str] = None
    status: JobStatus
    message: str
    results: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now) 