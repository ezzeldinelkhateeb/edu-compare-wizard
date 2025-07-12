from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import asyncio
import json
from pathlib import Path
import uuid
from datetime import datetime

# Import services (with fallback for missing services)
try:
    from ...services.multilingual_processor import MultilingualProcessor
    multilingual_processor = MultilingualProcessor()
except ImportError:
    multilingual_processor = None

try:
    from ...services.enhanced_comparison_service import EnhancedComparisonService, ComparisonConfig
    comparison_service = EnhancedComparisonService()
except ImportError:
    comparison_service = None

try:
    from ...services.batch_processor import BatchProcessor, BatchProcessingConfig
    batch_processor = BatchProcessor()
except ImportError:
    batch_processor = None

from ...core.config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/test")
async def test_multilingual_endpoint():
    """Test endpoint for multilingual features"""
    return {
        "message": "Multilingual comparison endpoints are working",
        "services_available": {
            "multilingual_processor": multilingual_processor is not None,
            "comparison_service": comparison_service is not None,
            "batch_processor": batch_processor is not None
        },
        "timestamp": datetime.now().isoformat()
    }

@router.post("/detect-language")
async def detect_content_language(
    content: str = Form(...),
    confidence_threshold: float = Form(0.6)
):
    """Detect the language of provided content"""
    if not multilingual_processor:
        raise HTTPException(status_code=500, detail="Multilingual processor not available")
    
    try:
        detected_lang, confidence = multilingual_processor.detect_content_language(content)
        
        return {
            "detected_language": detected_lang,
            "confidence": confidence,
            "is_confident": confidence >= confidence_threshold,
            "supported": detected_lang in multilingual_processor.supported_languages,
            "language_info": multilingual_processor.supported_languages.get(detected_lang, {}).name if detected_lang in multilingual_processor.supported_languages else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages and their configurations"""
    if not multilingual_processor:
        raise HTTPException(status_code=500, detail="Multilingual processor not available")
    
    try:
        languages = {}
        for code, config in multilingual_processor.supported_languages.items():
            languages[code] = {
                "name": config.name,
                "native_name": config.name,  # You might want to add native names
                "rtl": config.rtl,
                "confidence_threshold": config.confidence_threshold
            }
        
        return {
            "supported_languages": languages,
            "default_language": "auto",
            "total_supported": len(languages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language info retrieval failed: {str(e)}")

# Placeholder endpoints for future implementation
@router.post("/process-content")
async def process_multilingual_content_placeholder():
    """Placeholder for content processing"""
    return {
        "message": "Content processing endpoint - under development",
        "status": "placeholder"
    }

@router.post("/enhanced-compare")
async def enhanced_content_comparison_placeholder():
    """Placeholder for enhanced comparison"""
    return {
        "message": "Enhanced comparison endpoint - under development", 
        "status": "placeholder"
    }

@router.post("/batch-upload")
async def batch_file_upload_placeholder():
    """Placeholder for batch upload"""
    return {
        "message": "Batch upload endpoint - under development",
        "status": "placeholder"
    }