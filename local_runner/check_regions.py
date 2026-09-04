import runpod
import os
from dotenv import load_dotenv

load_dotenv()
runpod.api_key = os.getenv("RUNPOD_API_KEY")

try:
    # Just a dummy pod create to see the error or available regions if possible
    # Actually let's try to get regions if the SDK supports it
    print("Checking for regions...")
    # The SDK doesn't have a direct get_regions in all versions, let's try to find it
    # But usually, it's safer to just specify the one the user told us.
    pass
except Exception as e:
    print(f"Error: {e}")
