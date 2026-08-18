#!/usr/bin/env python3
import sys
print("Python path:", sys.path)
print("\nTrying to import config...")

try:
    import config
    print("Config imported successfully")
    print("Config attributes:", dir(config))
    
    if hasattr(config, 'DATABASE_CONFIG'):
        print("DATABASE_CONFIG found:", config.DATABASE_CONFIG)
    else:
        print("DATABASE_CONFIG NOT found")
        
except Exception as e:
    print(f"Error importing config: {e}")
    import traceback
    traceback.print_exc()

print("\nTrying to import dotenv...")
try:
    from dotenv import load_dotenv
    print("dotenv imported successfully")
    result = load_dotenv()
    print(f"load_dotenv() result: {result}")
except Exception as e:
    print(f"Error with dotenv: {e}")
    import traceback
    traceback.print_exc()
