import asyncio
import time
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from rich import print as rprint


async def main():
    load_dotenv()

    Monument = Literal[
        "Eiffel Tower",
        "Louvre Museum",
        "Notre-Dame Cathedral",
        "Arc de Triomphe",
        "Sacré-Cœur",
        "Palace of Versailles",
        "Musée d'Orsay",
        "Centre Pompidou",
        "Sainte-Chapelle",
        "Luxembourg Gardens",
        "Tuileries Garden",
        "Pantheon",
        "Place de la Concorde",
        "Champs-Élysées",
        "Montmartre",
        "Seine River Cruise",
        "Disneyland Paris",
        "Catacombs of Paris",
        "Père Lachaise Cemetery",
        "Rodin Museum",
        "Grand Palais",
        "Petit Palais",
        "Place Vendôme",
        "Les Invalides",
        "Moulin Rouge",
        "Opéra Garnier",
        "Galeries Lafayette",
        "Printemps Haussmann",
        "La Défense",
        "Parc des Buttes-Chaumont",
        "Parc de la Villette",
        "Canal Saint-Martin",
        "Belleville Neighborhood",
        "Marché aux Puces de Saint-Ouen",
        "Parc Monceau",
        "Jardin des Plantes",
        "Cimetière du Montparnasse",
        "Institut du Monde Arabe",
    ]

    class OneWay(BaseModel):
        mode: str = Field(..., description="Mode of transportation.")
        duration: int = Field(..., description="Duration in minutes.")
        length_km: float = Field(..., description="Length in kilometers.")

    class Tour(BaseModel):
        outward: OneWay | list[OneWay] | None
        inward: OneWay | list[OneWay] | None
        sub_tours: list["Tour"] | None

    class Journey(BaseModel):
        tours: list[Tour] = Field(..., description="List of tours in the journey.")
        people: int = Field(..., description="Number of people traveling.")
        people_names: list[str] = Field(
            ..., description="Names of the people traveling."
        )
        monuments: list[Monument] = Field(
            ..., description="List of monuments to visit during the journey."
        )

    journey = """
    - tour 1:
        - Outward journey:
        - Mode: Train
        - Duration: 120 minutes
        - Length: 200 km
        - Inward journey:
        - Mode: Car
        - Duration: 150 minutes
        - Length: 220 km
        - Sub-tours:
        - Outward journey:
            - Mode: Bus
            - Duration: 60 minutes
            - Length: 80 km
        - Inward journey:
            - Mode: Bicycle
            - Duration: 90 minutes
            - Length: 100 km
    
    people_names = ["Alice", "Bob", "Charlie"]
    monuments = ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral"]
    
    """

    prompt = f"""Extract structured information about a round trip journey from the following description. 

    Description:
    {journey}
    """

    models: dict[str, BaseChatModel] = {
        "gpt": ChatOpenAI(model="gpt-5.2", reasoning={"effort": "none"}),
        # "claude": ChatAnthropic(  # pyright: ignore
        #     model_name="claude-sonnet-4-5"
        # ),
        # "gemini": ChatGoogleGenerativeAI(
        #     model="gemini-2.5-pro",
        #     project="mueller-inki-labeltranslator",
        #     thinking_budget=128,
        # ),
    }

    # fc_models = {
    #     f"{k}-fc": m.with_structured_output(
    #         Tour, method="function_calling", include_raw=True
    #     )
    #     for k, m in models.items()
    # }
    cd_models = {
        f"{k}-cd": m.with_structured_output(
            Journey, method="json_schema", include_raw=True
        )
        for k, m in models.items()
    }

    json_models = cd_models

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
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    rprint(f"[bold blue]Elapsed time {end_time - start_time} seconds[/bold blue]")
