## Under the Hood
### Quick LLM Refresher

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

--

## Under the Hood
### Where Constrained Decoding Fits

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

--

## Under the Hood
### The Key Insight

Constrained decoding is just a **mask** on the final distribution.

- The model itself is unchanged
- No fine-tuning required
- No architectural changes
- Just: "which tokens are grammatically valid here?"

The magic is in computing that mask **fast**.

--

## Under the Hood
### Evolution of Implementations

**Outlines (2023)** — Original approach
- Precompute lookup table: `(state, token) → valid?`
- Problem: huge table, minutes to build for complex schemas
- Paper: "Efficient Guided Generation for Large Language Models"

**llguidance (2025)** — Current state of the art
- Computes valid tokens on-the-fly
- Uses trie pruning + smart regex-like checks
- ~2ms startup, ~50μs per token
- Now used by OpenAI, llama.cpp, vLLM...
- Integrated with transformers
