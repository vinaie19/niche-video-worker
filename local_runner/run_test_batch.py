import os
import time
import runpod
from dotenv import load_dotenv
from test_prompts import test_jobs

load_dotenv()

runpod.api_key = os.getenv("RUNPOD_API_KEY")

def run_batch():
    # This is a simplified version of how to trigger the jobs.
    # In a real scenario, you'd likely use the runpod SDK to start a pod 
    # if it's not already running, or use a serverless endpoint.
    
    # Example for serverless endpoint (assuming you've deployed it):
    endpoint_id = "YOUR_ENDPOINT_ID" 
    endpoint = runpod.Endpoint(endpoint_id)

    for job_data in test_jobs:
        video_id = job_data["video_id"]
        print(f"🚀 Starting video: {video_id}")
        
        for i, shot_prompt in enumerate(job_data["shots"]):
            print(f"  🎬 Processing Shot {i+1}...")
            
            run_request = endpoint.run({
                "input": {
                    "prompt": shot_prompt,
                    "video_id": video_id,
                    "shot_index": i + 1
                }
            })
            
            # Wait for result
            result = run_request.output()
            print(f"  ✅ Shot {i+1} complete: {result.get('output_r2_url')}")

if __name__ == "__main__":
    if os.getenv("RUNPOD_API_KEY") == "your_runpod_api_key":
        print("❌ Please update local_runner/.env with your actual API keys!")
    else:
        run_batch()
