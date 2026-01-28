## Practical Considerations
### Schema Limitations

Not all JSON Schema features are supported:

- **Recursion depth**: Usually limited (e.g., max 10 levels)
- **`additionalProperties`**: Must be `false` (OpenAI)
- **`required`**: All properties must be listed (OpenAI)
- **`anyOf` / `oneOf`**: Partial or no support

Always check your provider's documentation!

--

## Practical Considerations
### Quality Tradeoffs

Research shows constraints can degrade output quality:

**The problem:**
- Model "wants" to output token A (high probability)
- Grammar only allows token B (low probability)
- Forcing B may cause downstream issues

**For JSON:** Usually fine — LLMs are heavily trained on JSON.

**Edge cases:** Very unusual schemas, rare enum values, deep nesting.

> Sometimes malformed JSON with correct content > valid JSON with hallucinated content. At least something breaks instead of silently failing.

--

## Practical Considerations
### Temperature Settings

Low temperature is generally safer with constraints.

High temperature + strict constraints can force unlikely tokens.

--

## Practical Considerations
### Field Ordering Matters!

LLMs generate left-to-right. Schema field order affects generation:

```json
// ❌ Bad: reasoning after answer
{
  "score_1": 1,
  "reasoning_1": "Because I could not find..."
}

// ✅ Good: reasoning before answer  
{
  "reasoning_1": "Because I could not find...",
  "score_1": 0
}
```

Put reasoning/context fields **before** answer fields.

--

## Practical Considerations
### Thinking + Constraints = 🔥

Constrained decoding works with reasoning models for most "big" providers.

The constraint applies only to the **final output**, not to internal reasoning tokens.

The model can "think" freely, then produce guaranteed-valid JSON.
