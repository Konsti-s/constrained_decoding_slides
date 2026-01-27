import asyncio
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from rich import print as rprint

IngredientName = Literal[
    "tomatoe",
    "potatoe",
    "oinon",
    "garlicc",
    "carott",
    "celary",
    "brocoli",
    "spinnach",
    "letuce",
    "cucmber",
    "peppar",
    "mushroms",
    "zuchini",
    "egplant",
    "aspargus",
    "cauliflour",
    "cabagge",
    "beets",
    "radishs",
    "parsely",
    "cilantro",
    "basill",
    "oregeno",
    "thime",
    "rosemery",
    "chickn",
    "beaf",
    "prok",
    "salman",
    "shrimpp",
    "tunna",
    "lobbster",
    "baccon",
    "sausege",
    "hamburgur",
    "cheeze",
    "buttar",
    "milkk",
    "yogart",
    "creame",
    "flower",
    "suger",
    "saltt",
    "peper",
    "cinamon",
    "vanila",
    "chocolat",
    "honney",
    "mapel syrup",
    "olivve oil",
    "vinagar",
    "mustrad",
    "ketchep",
    "mayonaise",
    "wein",
]


async def main():
    loaded = load_dotenv()
    rprint(f"[bold blue]Loaded .env:[/bold blue] {loaded}")

    class Ingredient(BaseModel):
        """Schema for a single ingredient."""

        name: IngredientName = Field(..., description="Name of the ingredient.")
        quantity: str = Field(
            ...,
            description="Quantity of the ingredient as float. Examples: 1.5l, 250ml, 500kg.",
        )
        country: str = Field(
            ...,
            description="The precise origin of the ingredient as given on the packaging. "
            "Examples: 'Italy', 'California', 'France'.",
        )

    class Ingredients(BaseModel):
        """Return your response in this format."""

        ingredients: list[Ingredient]

    rprint(Ingredients.model_json_schema())

    ingredients = """
    - 100l of olive oile from Italy
    - 250ml of balsamic vinegaer from California
    - 500kg of floure from France
    - 200g of parmesan cheeze from Italy
    - 300g of sun-dried tomatoess from Spain
    - 1.5kg of fresh basil from Greece
    - 0.75l of red whine from France
    """

    prompt = f"""You are a helpful assistant that extracts structured information about ingredients from text. 
    Given a description of a list of ingredients, you will extract the name, quantity, and origin of each ingredient and return it.

    Your main task is to correct any misspellings in the ingredient names.

    So do not return the misspelled names, but always linguistically correct names.

    E.g. this is wrong: "tomatoe". The correct spelling is "tomato". Always use the correct spelling in your response.

    {ingredients}
    """

    models: dict[str, BaseChatModel] = {
        "gpt": ChatOpenAI(model="gpt-5.2"),
        "claude": ChatAnthropic(  # pyright: ignore
            model_name="claude-sonnet-4-5"
        ),
        "gemini": ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", project="mueller-inki-labeltranslator"
        ),
    }

    fc_models = {
        f"{k}-fc": m.with_structured_output(
            Ingredients, method="function_calling", include_raw=True
        )
        for k, m in models.items()
    }
    cd_models = {
        f"{k}-cd": m.with_structured_output(
            Ingredients, method="json_schema", include_raw=True
        )
        for k, m in models.items()
    }

    json_models = {**fc_models, **cd_models}

    coros = [model.ainvoke(prompt) for model in json_models.values()]

    responses = await asyncio.gather(*coros, return_exceptions=True)

    for (model_name, model), response in zip(json_models.items(), responses):
        rprint(f"[bold green]{model_name} response:[/bold green]")
        if isinstance(response, Exception):
            rprint(f"[bold red]Error:[/bold red] {response}")
        else:
            rprint(response)
        rprint("\n\n")


if __name__ == "__main__":
    asyncio.run(main())
