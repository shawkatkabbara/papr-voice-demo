import sys
import os
from dotenv import load_dotenv

load_dotenv()

sdk_path = "/Users/shawkatkabbara/Documents/GitHub/papr-pythonSDK/src"
sys.path.insert(0, sdk_path)

print("Starting import...")
import papr_memory
print("Import successful!")
