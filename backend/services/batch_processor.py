# backend/services/batch_processor.py

import os
import sys
from pathlib import Path
import concurrent.futures
import time
import argparse
import json
from tqdm import tqdm

# Ensure services can be imported
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.services.enhanced_comparison_service import SmartComparisonService
from backend.app.services.gemini_service import GeminiService
from backend.app.services.text_optimizer import TextOptimizer
# We might need to abstract the visual comparison logic into its own service
# For now, we can use the logic from simple_visual_test.py as a placeholder
from backend.simple_visual_test import compare_images as calculate_visual_similarity

class BatchProcessor:
    """
    Manages the batch processing of image comparisons using the smart pipeline.
    """
    def __init__(self, old_dir, new_dir, max_workers=5, visual_threshold=0.95):
        self.old_dir = Path(old_dir)
        self.new_dir = Path(new_dir)
        self.max_workers = max_workers
        self.visual_threshold = visual_threshold
        self.results = []
        self.summary = {
            "total_pairs": 0,
            "visually_identical": 0,
            "fully_analyzed": 0,
            "failed": 0,
            "start_time": time.time(),
            "end_time": 0,
            "total_duration": 0
        }
        # Placeholder for services that might be needed
        self.gemini_service = GeminiService()
        self.text_optimizer = TextOptimizer()
        self.comparison_service = SmartComparisonService() # This service will orchestrate the calls

    def find_common_files(self):
        """Finds common files between the two directories."""
        old_files = {f.name for f in self.old_dir.glob("*.jpg")}
        new_files = {f.name for f in self.new_dir.glob("*.jpg")}
        common_files = sorted(list(old_files.intersection(new_files)))
        self.summary["total_pairs"] = len(common_files)
        print(f"🔍 Found {len(common_files)} common files to compare.")
        return common_files

    def process_pair(self, filename):
        """
        Processes a single pair of images through the smart pipeline.
        This function will be executed by the thread pool.
        """
        old_path = str(self.old_dir / filename)
        new_path = str(self.new_dir / filename)
        
        try:
            # Stage 1: Visual Comparison
            visual_result = calculate_visual_similarity(old_path, new_path)
            visual_score = visual_result.get('combined', 0)

            if visual_score >= self.visual_threshold:
                self.summary["visually_identical"] += 1
                return {
                    "filename": filename,
                    "status": "Visually Identical",
                    "visual_score": visual_score,
                    "details": "Processing stopped at Stage 1. High visual similarity.",
                    "final_score": visual_score * 100
                }

            # If visual similarity is below the threshold, proceed with the full pipeline.
            # This simulates calling the full orchestration service.
            # In a real scenario, this service would handle stages 2, 3, and 4.
            # For this example, we'll mock the next steps.
            
            # Stages 2, 3, 4 (Orchestrated by SmartComparisonService)
            # This is a conceptual call. The actual implementation is in SmartComparisonService
            # result_json = self.comparison_service.compare_images(old_path, new_path)
            # For now, we will just return a placeholder result.
            
            self.summary["fully_analyzed"] += 1
            # Placeholder for Gemini result
            final_analysis = {
                "final_similarity_score": 85.5, # Mocked value
                "summary_of_changes": "Mock: Significant changes detected in the text content."
            }

            return {
                "filename": filename,
                "status": "Fully Analyzed",
                "visual_score": visual_score,
                "details": final_analysis["summary_of_changes"],
                "final_score": final_analysis["final_similarity_score"]
            }

        except Exception as e:
            self.summary["failed"] += 1
            return {
                "filename": filename,
                "status": "Failed",
                "error": str(e)
            }

    def run(self):
        """
        Executes the batch processing of all common files.
        """
        common_files = self.find_common_files()
        if not common_files:
            print("No common files to process. Exiting.")
            return

        print(f"🚀 Starting batch processing with up to {self.max_workers} parallel workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Using tqdm for a progress bar
            list_of_futures = [executor.submit(self.process_pair, f) for f in common_files]
            
            for future in tqdm(concurrent.futures.as_completed(list_of_futures), total=len(common_files)):
                self.results.append(future.result())

        self.summary["end_time"] = time.time()
        self.summary["total_duration"] = self.summary["end_time"] - self.summary["start_time"]
        self.print_results()

    def print_results(self):
        """
        Prints the results in a clear and organized format.
        """
        print("\n" + "="*60)
        print("📊 Detailed Comparison Results")
        print("="*60)

        # Sort results by filename for consistent output
        self.results.sort(key=lambda x: x['filename'])

        for res in self.results:
            print(f"\n🔄 Comparing: [{res['filename']}]")
            print(f"   Status: {res['status']}")
            if res['status'] == "Failed":
                print(f"   ❌ Error: {res.get('error')}")
            else:
                print(f"   Visual Score: {res.get('visual_score', 0):.2%}")
                print(f"   Final Score: {res.get('final_score', 0):.2f}%")
                print(f"   Details: {res.get('details')}")
            print("-" * 50)
        
        self.print_summary()

    def print_summary(self):
        """Prints the final summary of the batch job."""
        print("\n" + "="*60)
        print("📈 Batch Processing Summary")
        print("="*60)
        s = self.summary
        total = s['total_pairs']
        
        print(f"Total Pairs Processed: {total}")
        if total > 0:
            print(f"✅ Visually Identical (Skipped): {s['visually_identical']} ({s['visually_identical']/total:.1%})")
            print(f"🧠 Fully Analyzed: {s['fully_analyzed']} ({s['fully_analyzed']/total:.1%})")
            print(f"❌ Failed: {s['failed']} ({s['failed']/total:.1%})")
        
        duration = s.get('total_duration', 0)
        print(f"⏱️ Total Duration: {duration:.2f} seconds")
        if total > 0:
             print(f"   Average time per pair: {duration/total:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description="Batch process image comparisons.")
    parser.add_argument("old_dir", help="Directory with the old version images.")
    parser.add_argument("new_dir", help="Directory with the new version images.")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers.")
    parser.add_argument("--threshold", type=float, default=0.95, help="Visual similarity threshold to skip full analysis.")
    
    args = parser.parse_args()

    processor = BatchProcessor(
        old_dir=args.old_dir,
        new_dir=args.new_dir,
        max_workers=args.workers,
        visual_threshold=args.threshold
    )
    processor.run()

if __name__ == "__main__":
    # Example of how to run from command line:
    # python -m backend.services.batch_processor "test/2024" "test/2025" --workers 4
    main() 