## Beyond JSON: CFG Support

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
