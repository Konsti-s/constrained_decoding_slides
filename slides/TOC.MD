
# Timeline of JSON responses:
    - 2022: "Please return JSON" → unreliable, json_schema in prompt
    - June 2023: OpenAI Function Calling → big leap, still retry loops
    - Aug 2024: OpenAI Structured Outputs → guaranteed valid, constrained decoding
    - May 2025: OpenAI switches to llguidance → faster, broader schema support

# Provider support as of today for constrained decoding
   - OpenAI, Anthropic, Google: all support it
   - Schema support varies

# Under the hood
    - Really quick refresher on llms (generate a distribution over the vocabulary from which is sampled, in most cases greedily)
    - Explain where constrained decoding fits in (just masking the final distribution vector). Very small layer on top of the unchanged model during sampling.
    - links to the original paper and repo (Outlines), explain that it precomputed a table -> initial delay
    - link to the SOTA appraoch of guidance, explain the difference briefly and non-technical -> on the fly, using trie pruning and smart regex-like checks -> no initial delay
  
# Practical considerations
   - Schema limitations (depth, recursion, feature support (additionalProperties must be false for OpenAI e.g.)), , add link to the respective docus of openai, google, anthropic
   - Thinking + constrained_decoding together is boss
   - Temperature should be very low
   - Ordering of objects in  the schema matters a lot. Usually the order of generation must be the same as the order in the json_schema.
   - Quality tradeoffs (research findings) i.e. unlikely sequences being forced through cfg vs malformed json but correct content (i have a python code example highlighting this scenario)
   - Also tool calling itself can be forced to adhere to a CFG

# Use cases:
   - Extraction:
      - Data extraction from documents
      - Entity recognition with structure
    - Integration:
      - API call generation
      - Database query construction
    - Batch/Pipeline:
      - Processing tasks with shared context or contextual interdependence
      - Multi-step workflows with structured handoffs
    - Content:
        - Structured content generation
        - Form filling
  
# Beyond JSON: CFG Support
   - OpenAI's Lark grammar injection
   - Use cases: SQL, DSLs, custom formats