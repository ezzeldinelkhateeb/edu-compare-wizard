#!/usr/bin/env python3
"""
سكريپت سريع لتشغيل الخادم
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 تشغيل الخادم على المنفذ 8001...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True) 