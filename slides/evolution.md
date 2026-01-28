## Evolution
### 2022: The Dark Ages

```python
prompt = """
Extract user info. Return ONLY valid JSON:
{"name": string, "age": number}

Text: "Hi, I'm Alice and I'm 30 years old"
"""

response = llm(prompt)
try:
    data = json.loads(response)
except json.JSONDecodeError:
    # Try to extract JSON with regex
    # Or retry with "No really, ONLY JSON please"
    # Or give up
```

--

## Evolution
### June 2023: Function Calling

```python
response = openai.chat.completions.create(
    messages=[...],
    functions=[{
        "name": "extract_user",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
    }]
)
```

**Better!** But still not guaranteed. Retry loops still needed.

--

## Evolution
### Aug 2024: Structured Outputs

```python
response = openai.chat.completions.create(
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "user_info",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"]
            }
        }
    }
)
```

**Guaranteed valid.** No retry loops.

--

## Evolution
### Constrained Decoding Support Today

**It's fast**

**It's a standard, supported by most providers**

- OpenAI, Anthropic, Google Gemini, Mistral, xAI (Grok), Groq, ...
- Langchain tries to homogenize the zoo once again with a common interface.
- ⚠️ Schema feature support varies between providers
- Check each provider's documentation for exact limitations.


**What about self-hosted inference engines?**

- vLLM and SGLang (with xgrammar/llguidance backends)
- llama.cpp (GBNF grammars)
- Ollama (wraps llama.cpp)
- TGI (now in maintenance mode, HuggingFace recommends vLLM/SGLang)



