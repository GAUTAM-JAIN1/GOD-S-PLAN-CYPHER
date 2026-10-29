import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.services.groq_compiler import get_groq_client

client = get_groq_client()
models = [m.id for m in client.models.list().data]
print("AVAILABLE GROQ MODELS:")
for m in sorted(models):
    print(" -", m)
