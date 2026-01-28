import asyncio

from dotenv import load_dotenv
from langchain.chat_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from rich import print as rprint


async def main():
    load_dotenv()

    class IngredientsDict(BaseModel):
        """Return your response in this format."""

        ingredients: dict[str, str] = Field(
            ...,
            description="A dictionary mapping ingredient names to their quantities. "
            "For example: { 'olive oil': '100l', 'balsamic vinegar': '250ml' }",
        )

    class Ingredient(BaseModel):
        key: str = Field(..., description="Name of the ingredient.")
        value: str = Field(..., description="Quantity of the ingredient.")

    class IngredientsList(BaseModel):
        """Return your response in this format."""

        ingredients: list[Ingredient] = Field(
            ..., description="A list of ingredients with their quantities. "
        )

    ingredients = """
    - 100l of olive oil from Italy
    - 250ml of balsamic vinegar from California
    - 500kg of flour from France
    - 200g of parmesan cheese from Italy
    - 300g of sun-dried tomatoes from Spain
    - 1.5kg of fresh basil from Greece
    - 0.75l of red wine from France
    """

    prompt = f"""You are a helpful assistant that extracts structured information about ingredients from text. 
    Given a description of a list of ingredients, you will extract the name and quantity of each ingredient and return it.

    Make sure to return the exact quantity.

    Here is the list of ingredients:
    
    {ingredients}
    """

    models: dict[str, BaseChatModel] = {
        "claude": ChatAnthropic(  # pyright: ignore
            model_name="claude-sonnet-4-5"
        ),
        "gpt": ChatOpenAI(model="gpt-5.2"),
        "gemini": ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", project="mueller-inki-labeltranslator"
        ),
    }

    fc_models = {
        f"{k}-fc": m.with_structured_output(
            IngredientsDict, method="function_calling", include_raw=True
        )
        for k, m in models.items()
    }
    cd_models = {
        f"{k}-cd": m.with_structured_output(
            IngredientsDict, method="json_schema", include_raw=True
        )
        for k, m in models.items()
    }

    # fc_models = {
    #     f"{k}-fc": m.with_structured_output(
    #         IngredientsList, method="function_calling", include_raw=True
    #     )
    #     for k, m in models.items()
    # }
    # cd_models = {
    #     f"{k}-cd": m.with_structured_output(
    #         IngredientsList, method="json_schema", include_raw=True
    #     )
    #     for k, m in models.items()
    # }

    json_models = {**fc_models, **cd_models}

    coros = [model.ainvoke(prompt) for model in json_models.values()]

    responses = await asyncio.gather(*coros, return_exceptions=True)

    for (model_name, _), response in zip(json_models.items(), responses):
        rprint(f"[bold green]{model_name} response:[/bold green]")
        if isinstance(response, Exception):
            rprint(f"[bold red]Error:[/bold red] {response}")
        else:
            rprint(response)
        rprint("\n\n")


if __name__ == "__main__":
    asyncio.run(main())
