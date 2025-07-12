#!/usr/bin/env python3
"""
Run LandingAI extraction on a provided JPG image after adding fields_schema.
"""
import asyncio, os, sys
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.services.landing_ai_service import LandingAIService

async def main():
    image_path = r"C:\Users\ezz\Downloads\elkheta-content-compare-pro-main\elkheta-content-compare-pro-main\مقدمة تمهيدية.pdf"
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return
    service = LandingAIService()
    result = await service.extract_from_file(file_path=image_path)
    if result.success:
        print("✅ LandingAI extraction successful!")
        print(f"📄 Content length: {len(result.markdown_content)} characters")
    else:
        print(f"❌ Extraction failed: {result.error_message}")

if __name__ == '__main__':
    asyncio.run(main())