#!/usr/bin/env python3
"""
Simple test for OCR functionality
"""

import os
import sys
import json
from datetime import datetime

def test_ocr_basic():
    """Basic OCR test using Tesseract"""
    print("🔍 Testing OCR functionality...")
    
    # Check if image exists
    image_path = "103.jpg"
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    print(f"📸 Found image: {image_path}")
    print(f"📊 File size: {os.path.getsize(image_path)} bytes")
    
    try:
        # Try to import required libraries
        import pytesseract
        from PIL import Image
        import cv2
        import numpy as np
        
        print("✅ All required libraries imported successfully")
        
        # Load and process image
        print("📸 Loading image...")
        image = Image.open(image_path)
        print(f"📊 Image info: {image.width}x{image.height} ({image.format})")
        
        # Convert to numpy array for processing
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            print("🔄 Converted to grayscale")
        else:
            img_gray = img_array
        
        # Basic image enhancement
        print("🔧 Enhancing image...")
        
        # Apply Gaussian blur to reduce noise
        img_blur = cv2.GaussianBlur(img_gray, (1, 1), 0)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img_enhanced = clahe.apply(img_blur)
        
        # Apply threshold to get binary image
        _, img_thresh = cv2.threshold(img_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        print("✅ Image preprocessing completed")
        
        # OCR extraction
        print("📝 Starting OCR extraction...")
        
        # Try different OCR configurations
        ocr_configs = [
            ("ara+eng", "--oem 3 --psm 6"),
            ("ara", "--oem 3 --psm 4"),
            ("eng", "--oem 3 --psm 6"),
            ("ara+eng", "--oem 3 --psm 3")
        ]
        
        best_text = ""
        best_confidence = 0
        
        for lang, config in ocr_configs:
            try:
                print(f"🔄 Trying: {lang} - {config}")
                
                # Extract text with confidence
                data = pytesseract.image_to_data(
                    img_thresh, 
                    lang=lang, 
                    config=config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Extract text
                text = pytesseract.image_to_string(
                    img_thresh, 
                    lang=lang, 
                    config=config
                )
                
                print(f"   Confidence: {avg_confidence:.1f}%, Text length: {len(text)}")
                
                if avg_confidence > best_confidence and text.strip():
                    best_confidence = avg_confidence
                    best_text = text
                    print(f"   ✅ New best result!")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                continue
        
        if best_text:
            print(f"\n✅ OCR completed successfully!")
            print(f"🎯 Best confidence: {best_confidence:.1f}%")
            print(f"📝 Extracted text ({len(best_text)} characters):")
            print("-" * 50)
            print(best_text)
            print("-" * 50)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = f"ocr_test_results_{timestamp}"
            os.makedirs(results_dir, exist_ok=True)
            
            # Save extracted text
            text_path = os.path.join(results_dir, "extracted_text.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(best_text)
            
            # Save OCR details
            details_path = os.path.join(results_dir, "ocr_details.json")
            with open(details_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "confidence": best_confidence,
                    "text_length": len(best_text),
                    "word_count": len(best_text.split()),
                    "timestamp": timestamp,
                    "image_info": {
                        "path": image_path,
                        "size": os.path.getsize(image_path),
                        "dimensions": f"{image.width}x{image.height}",
                        "format": image.format
                    }
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Results saved to: {results_dir}")
            print(f"📄 Text file: {text_path}")
            print(f"📊 Details file: {details_path}")
            
            return True
        else:
            print("❌ No text extracted")
            return False
            
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        print("Please install required packages:")
        print("pip install pytesseract pillow opencv-python numpy")
        return False
    except Exception as e:
        print(f"❌ Error during OCR: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Simple OCR Test")
    print("=" * 50)
    
    success = test_ocr_basic()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 