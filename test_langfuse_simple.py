"""Simple LangFuse integration test"""
import os
import sys
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

# Check environment variables
print("=== Environment Variables ===")
print(f"LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')}")
print(f"LANGFUSE_SECRET_KEY: {os.getenv('LANGFUSE_SECRET_KEY', 'NOT SET')}")
print(f"LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'NOT SET')}")
print()

# Test LangFuse import
print("=== LangFuse Import Test ===")
try:
    from langfuse import observe, Langfuse
    print("[PASS] langfuse imported successfully")
except ImportError as e:
    print(f"[FAIL] langfuse import failed: {e}")
    sys.exit(1)

# Test LangFuse initialization
print()
print("=== LangFuse Initialization Test ===")
try:
    langfuse = Langfuse()
    print(f"[PASS] Langfuse client created")
    print(f"       public_key configured: {bool(langfuse.public_key)}")
    print(f"       secret_key configured: {bool(langfuse.secret_key)}")
    print(f"       host: {langfuse.host}")
except Exception as e:
    print(f"[FAIL] Langfuse initialization failed: {e}")

# Test auth check
print()
print("=== LangFuse Auth Check ===")
try:
    result = langfuse.auth_check()
    print(f"[PASS] Auth check result: {result}")
except Exception as e:
    print(f"[FAIL] Auth check failed: {e}")

# Test @observe decorator
print()
print("=== @observe Decorator Test ===")

@observe(name="test_function")
def test_function():
    return "Hello from observed function"

try:
    result = test_function()
    print(f"[PASS] @observe decorator works: {result}")
    print(f"       function has __wrapped__: {hasattr(test_function, '__wrapped__')}")
except Exception as e:
    print(f"[FAIL] @observe decorator failed: {e}")

# Test LLM Client import
print()
print("=== LLM Client Import Test ===")
try:
    from engines.common.llm_client import LLMClient, LANGFUSE_AVAILABLE
    print(f"[PASS] LLMClient imported")
    print(f"       LANGFUSE_AVAILABLE: {LANGFUSE_AVAILABLE}")
    print(f"       invoke has @observe: {hasattr(LLMClient.invoke, '__wrapped__')}")
    print(f"       stream_invoke has @observe: {hasattr(LLMClient.stream_invoke, '__wrapped__')}")
    print(f"       structured_invoke has @observe: {hasattr(LLMClient.structured_invoke, '__wrapped__')}")
except Exception as e:
    print(f"[FAIL] LLMClient import failed: {e}")

# Flush LangFuse
print()
print("=== Flush LangFuse ===")
try:
    langfuse.flush()
    print("[PASS] LangFuse flushed successfully")
except Exception as e:
    print(f"[FAIL] LangFuse flush failed: {e}")

print()
print("=== Test Complete ===")
