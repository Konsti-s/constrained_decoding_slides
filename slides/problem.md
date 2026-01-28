## The Problem

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
