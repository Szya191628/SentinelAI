"""测试 LangFuse 追踪是否真正生效"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from langfuse import Langfuse, observe
import time

print("=== 1. 初始化 LangFuse 客户端 ===")
langfuse = Langfuse()
print(f"Auth check: {langfuse.auth_check()}")

print()
print("=== 2. 测试手动创建 Trace ===")
try:
    # 手动创建一个 trace
    trace = langfuse.trace(
        name="test-trace",
        input={"query": "test query"},
        metadata={"test": True},
    )
    print(f"Trace created: {trace.id}")

    # 在 trace 下创建一个 span
    span = trace.span(
        name="test-span",
        input={"step": 1},
    )
    span.end(output={"result": "success"})
    print(f"Span created and ended")

    # 在 trace 下创建一个 generation
    generation = trace.generation(
        name="test-llm-call",
        model="test-model",
        input=[{"role": "user", "content": "hello"}],
        output="Hello! How can I help you?",
        usage={"input": 10, "output": 20},
    )
    print(f"Generation created")

    # 刷新确保数据发送
    print("Flushing...")
    langfuse.flush()
    time.sleep(2)  # 等待数据发送
    print(f"Trace URL: {trace.get_trace_url()}")
    print()
    print("请访问上面的 URL 查看 Trace")
    print()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=== 3. 测试 @observe 装饰器 ===")

@observe(name="test_decorated_function")
def my_test_function(input_text: str) -> str:
    """一个被 @observe 装饰的测试函数"""
    return f"Processed: {input_text}"

try:
    result = my_test_function("hello world")
    print(f"Function result: {result}")
    print("Flushing...")
    langfuse.flush()
    time.sleep(2)
    print("Done - check LangFuse dashboard for traces")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
