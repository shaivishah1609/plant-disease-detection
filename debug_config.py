import sys
import os

print("Working directory:", os.getcwd())
print("\nAttempting to import config...")

# Direct module loading
import importlib.util
spec = importlib.util.spec_from_file_location("config", "config.py")
config = importlib.util.module_from_spec(spec)

print("\nConfig module created:", config)
print("About to execute module...")

try:
    spec.loader.exec_module(config)
    print("Module executed successfully")
    print("Config attributes:", [attr for attr in dir(config) if not attr.startswith('_')])
    if hasattr(config, 'DATABASE_CONFIG'):
        print("\nDATABASE_CONFIG found:", config.DATABASE_CONFIG)
except Exception as e:
    print(f"Error executing module: {e}")
    import traceback
    traceback.print_exc()
