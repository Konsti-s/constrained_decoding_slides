import textwrap

from dotenv import load_dotenv
from openai import OpenAI
from rich import print as rprint

constrained_lark_mssql_grammar = textwrap.dedent(r"""
            // ---------- Terminals ----------
            SP: " "
            COMMA: ","
            GT: ">"
            EQ: "="
            SEMI: ";"
            IDENTIFIER: /[A-Za-z_][A-Za-z0-9_]*/
            NUMBER: /[0-9]+/
            DATE: /'[0-9]{4}-[0-9]{2}-[0-9]{2}'/

            // ---------- Rules ----------
            select_list: column (COMMA SP column)*
            column: IDENTIFIER
            table: IDENTIFIER
            amount_filter: "total_amount" SP GT SP NUMBER
            date_filter: "order_date" SP GT SP DATE
            sort_cols: "order_date" SP "DESC"

            // ---------- Entry point ----------
            // looks like: SELECT TOP <number> <columns> FROM <table> WHERE <filter1> AND <filter2> ORDER BY <sort> ;
            start: "SELECT" SP "TOP" SP NUMBER SP select_list SP "FROM" SP table SP "WHERE" SP amount_filter SP "AND" SP date_filter SP "ORDER" SP "BY" SP sort_cols SEMI
    """)


load_dotenv()
client = OpenAI()

sql_prompt_mssql = (
    "Call the mssql_grammar to generate a query for Microsoft SQL Server that retrieve the "
    "five most recent orders per customer, showing customer_id, order_id, order_date, and total_amount, "
    "where total_amount > 500 and order_date is after '2025-01-01'. "
)

response_mssql = client.responses.create(
    model="gpt-5.2",
    input=sql_prompt_mssql,
    text={"format": {"type": "text"}},
    tools=[
        {
            "type": "custom",
            "name": "mssql_grammar",
            "description": "Executes read-only Microsoft SQL Server queries limited to SELECT statements with TOP and basic WHERE/ORDER BY.",
            "format": {
                "type": "grammar",
                "syntax": "lark",
                "definition": constrained_lark_mssql_grammar,
            },
        },
    ],
    reasoning={"effort": "medium"},
    parallel_tool_calls=False,
)


rprint(response_mssql.output[1].input)  # pyright: ignore
