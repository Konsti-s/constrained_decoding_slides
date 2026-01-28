# Constrained Decoding for Structured Outputs
## Getting Guaranteed JSON from LLMs

---

# The Problem

```python
response = llm("Extract the user's name and age. Return JSON.")

# Response: "Sure! Here's the JSON: {"name": "Alice", "age": 30}"
#           ↑ Extra text breaks parsing

# Response: {"name": "Alice", "age": "thirty"}
#                                    ↑ Wrong type

# Response: {"name": "Alice, age: 30}
#                          ↑ Missing quotes, invalid JSON
```

**The old solution:** Retry loops, regex extraction, prayer 🙏

---

# Timeline: How We Got Here

| Year | Approach | Reliability |
|------|----------|-------------|
| 2022 | "Please return JSON" in prompt | 😬 |
| June 2023 | Provider Function Calling | 😊 |
| Aug 2024 | Constrained Decoding | 😎 |
| May 2025 | Fast implementations (llguidance) | 🚀 |

---

# 2022: The Dark Ages

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

---

# June 2023: Function Calling

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

---

# Aug 2024: Structured Outputs

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
---

# Provider Support Today

Its a standard, Supported by

- **OpenAI**
- **Anthropic**
- **Google Gemini**
- ...

⚠️ Schema feature support varies between providers

Check each provider's documentation for exact limitations.

---

# Under the Hood
## Quick LLM Refresher

```
Input: "The capital of France is"
                ↓
         [ LLM Forward Pass ]
                ↓
Logits: [Paris: 8.2, London: 3.1, the: 2.8, ..., pizza: -5.0]
                ↓
         [ Softmax ]
                ↓
Probs:  [Paris: 0.72, London: 0.04, the: 0.03, ..., pizza: 0.0001]
                ↓
         [ Sample ]
                ↓
Output: "Paris"
```

---

# Under the Hood
## Where Constrained Decoding Fits

```
Input: "Return JSON: {"name":"
                ↓
         [ LLM Forward Pass ]
                ↓
Logits: [Alice: 5.2, }: 4.8, Bob: 4.5, ,: 3.2, 123: 2.1, ...]
                ↓
         [ Constrained Decoding Mask ]   ← NEW!
         
         Grammar says: expecting string content
         Invalid tokens: }, ,, 123, [, ...
                ↓
Masked: [Alice: 5.2, -∞, Bob: 4.5, -∞, -∞, ...]
                ↓
         [ Softmax + Sample ]
                ↓
Output: "Alice"    ✓ Guaranteed valid continuation
```

---

# Under the Hood
## The Key Insight

Constrained decoding is just a **mask** on the final distribution.

- The model itself is unchanged
- No fine-tuning required
- No architectural changes
- Just: "which tokens are grammatically valid here?"

The magic is in computing that mask **fast**.

---

# Under the Hood
## Evolution of Implementations

**Outlines (2023)** — Original approach
- Precompute lookup table: `(state, token) → valid?`
- Problem: huge table, minutes to build for complex schemas
- Paper: "Efficient Guided Generation for Large Language Models"

**llguidance (2025)** — Current state of the art
- Compute valid tokens on-the-fly
- Uses trie pruning + smart regex-like checks
- ~2ms startup, ~50μs per token
- Now used by OpenAI, llama.cpp, vLLM...
- Integrated with transformers

---

# Practical Considerations
## Schema Limitations

Not all JSON Schema features are supported:

- **Recursion depth**: Usually limited (e.g., max 10 levels)
- **`additionalProperties`**: Must be `false` (OpenAI)
- **`required`**: All properties must be listed (OpenAI)
- **`anyOf` / `oneOf`**: Partial or no support

Always check your provider's documentation!

---

# Practical Considerations
## Thinking + Constraints = 🔥

Constrained decoding works with reasoning models

The constraint applies only to the **final output**, not to internal reasoning tokens.

The model can "think" freely, then produce guaranteed-valid JSON.

---

# Practical Considerations
## Temperature Settings

Low temperature is generally safer with constraints:

High temperature + strict constraints can force unlikely tokens.

---

# Practical Considerations
## Field Ordering Matters!

LLMs generate left-to-right. Schema field order affects generation:

```json
// ❌ Bad: reasoning after answer
{
  "answer": 42,
  "reasoning": "Because 6 × 7 = 42"
}

// ✅ Good: reasoning before answer  
{
  "reasoning": "The question asks for 6 × 7. 6 × 7 = 42.",
  "answer": 42
}
```

Put reasoning/context fields **before** answer fields.

---

# Practical Considerations
## Quality Tradeoffs

Research shows constraints can degrade output quality:

**The problem:**
- Model "wants" to output token A (high probability)
- Grammar only allows token B (low probability)
- Forcing B may cause downstream issues

**For JSON:** Usually fine — LLMs are heavily trained on JSON.

**Edge cases:** Very unusual schemas, rare enum values, deep nesting.

Sometimes malformed JSON with correct content > valid JSON with hallucinated content. At least something breaks instead of silently failing.


---

# Use Cases
## Data Extraction

```python
schema = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "revenue": {"type": "number"},
        "year": {"type": "integer"},
        "currency": {"enum": ["USD", "EUR", "GBP"]}
    }
}

# Input: "Acme Corp reported $5.2M revenue in 2024"
# Output: {"company": "Acme Corp", "revenue": 5200000, 
#          "year": 2024, "currency": "USD"}
```

---

# Use Cases
## API Call Generation

```python
schema = {
    "type": "object",
    "properties": {
        "endpoint": {"type": "string"},
        "method": {"enum": ["GET", "POST", "PUT", "DELETE"]},
        "params": {"type": "object"}
    }
}

# "Get user 123's profile"
# → {"endpoint": "/users/123", "method": "GET", "params": {}}
```

---

# Use Cases
## Batch Processing

Process multiple items with shared context or contextual interdependence.
Determine output schema programatically during runtime according to the task.

- Simple tasks on many small texts with a large context prompt
- Translation of multiple small chunks of text

Consistent processing, structure, and context across all items in batch.

---

# Use Cases
## Structured Content Generation

```python
schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "content": {"type": "string"}
                }
            }
        },
        "tags": {"type": "array", "items": {"type": "string"}}
    }
}
```

Generate structured documents, forms, reports.

---

# Beyond JSON: CFG Support

OpenAI supports full context-free grammars via Lark syntax:

```python
sql_grammar = r"""
    start: select_stmt
    select_stmt: "SELECT" columns "FROM" table
    columns: IDENTIFIER ("," IDENTIFIER)*
    table: IDENTIFIER
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
"""

tools=[{
    "type": "custom",
    "name": "sql_query",
    "format": {
        "type": "grammar",
        "syntax": "lark",
        "definition": sql_grammar
    }
}]
```

---

# Summary

1. **Constrained decoding guarantees valid structured output**
2. **All major providers support it** (with varying schema features)
3. **It's just a mask** — no model changes needed
4. **Modern implementations are fast** — no startup delay
5. **Combine with reasoning** — constraints apply to final output only
6. **Order your schema fields thoughtfully** — reasoning before answers
7. **Beyond JSON** — CFG support for SQL, DSLs, custom formats

---

# Resources

- [**Outlines Paper**](https://arxiv.org/pdf/2307.09702) and [**Outlines Repo**](https://github.com/dottxt-ai/outlines)
- [**llguidance**](https://github.com/guidance-ai/guidance)
- [**OpenAI docs**](https://platform.openai.com/docs/guides/structured-outputs#supported-schemas)
- [**Anthropic docs**](https://platform.claude.com/docs/en/build-with-claude/structured-outputs#json-schema-limitations)
- [**Google docs**](https://ai.google.dev/gemini-api/docs/structured-output?example=recipe#json_schema_support)
