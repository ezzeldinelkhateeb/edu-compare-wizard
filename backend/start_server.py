#!/usr/bin/env python3
"""
سكريبت تشغيل بسيط للخادم
Simple server startup script
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 تشغيل FastAPI Server...")
    print("🌐 http://localhost:8000")
    print("📚 http://localhost:8000/docs")
    print("❤️  http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    ) 