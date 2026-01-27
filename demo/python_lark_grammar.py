from dotenv import load_dotenv
from openai import OpenAI
from rich import print as rprint

with open("python.lark", "r") as f:
    python_grammar = f.read()


load_dotenv()
client = OpenAI()

python_prompt = "Call the python_grammar to generate a Python code snippet that defines a function to calculate the factorial of a number."

response_python = client.responses.create(
    model="gpt-5.2",
    input=python_prompt,
    text={"format": {"type": "text"}},
    tools=[
        {
            "type": "custom",
            "name": "python_grammar",
            "description": "Executes Python code generation limited to function definitions and basic statements.",
            "format": {
                "type": "grammar",
                "syntax": "lark",
                "definition": python_grammar,
            },
        },
    ],
    reasoning={"effort": "medium"},
    parallel_tool_calls=False,
)


rprint(response_python.output[1].input)  # pyright: ignore
