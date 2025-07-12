import os
import sys

# تعيين متغير البيئة مباشرة
os.environ["VISION_AGENT_API_KEY"] = "ZzhobnJ6Z3J3cm1maW83Mnd3YW1sOmlCdGdzRVJWNDJSODNQSzdHbWNzVEdhZkFxSGNaWmdH"

from agentic_doc.parse import parse

print("Testing agentic_doc.parse...")

file_path = r"103.jpg"

try:
    print(f"Processing file: {file_path}")
    result = parse(file_path)
    
    print("\n===== SUCCESS =====")
    print(f"Number of results: {len(result)}")
    
    if len(result) > 0:
        doc_result = result[0]
        
        if hasattr(doc_result, 'markdown'):
            markdown_text = doc_result.markdown
            print(f"Markdown length: {len(markdown_text)} characters")
            print(f"First 200 chars: {markdown_text[:200]}")
        
        if hasattr(doc_result, 'chunks'):
            chunks = doc_result.chunks
            print(f"Number of chunks: {len(chunks)}")
            
            # Count chunk types
            chunk_types = {}
            for chunk in chunks:
                chunk_type = chunk.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            print(f"Chunk types: {chunk_types}")
        
        if hasattr(doc_result, 'result_path'):
            print(f"Result saved at: {doc_result.result_path}")
    
    print("===================")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc() 