# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService

from .firestore_tools import (
    list_animals,
    get_animal_details,
    report_animal_sighting,
    toggle_watchlist_alert,
)
from .weather_tools import get_zoo_weather_and_visibility_impact
from .image_tools import generate_animal_badge_image


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback


MODEL = "gemini-3.8-flash"
PROJECT_ID = "qwiklabs-gcp-03-2f3e1ba5c32a"
LOCATION = "us-east1"
MEMORY_BANK_ID = "5568585490522701824"
AGENT_ENGINE_RESOURCE_NAME = f"projects/512866960510/locations/{LOCATION}/reasoningEngines/2855096346287800320"


# Memory Bank Service builder for deployed Agent Runtime
def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )


# Write: send session events to Memory Bank for extraction across sessions
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


# Sandbox code executor for secure computation using Agent Platform
sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME
)


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are ZooNow, the smart companion assistant for visitors at the Toronto Zoo. "
        "You always remember every ANIMAL NAME, species, favorite animal, or exhibit that the visitor mentions, "
        "asks about, or sees, and recall them across sessions to personalize their zoo trip. "
        "You help visitors discover live animal availability and exhibit visibility, "
        "check live zoo weather conditions to assess whether animals are outdoors or seeking shelters, "
        "look up current crowd/official status reports, record sightings when visitors see or don't see an animal, "
        "manage their 'Notify Me When Available' watchlists, generate visual animal badges/illustrations on request, "
        "and provide recommendations on which exhibits to see now or check back later."
    ),
    workflow_description="Analyze the request, call available tools to fetch or record live zoo data, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_animals,
        get_animal_details,
        report_animal_sighting,
        toggle_watchlist_alert,
        get_zoo_weather_and_visibility_impact,
        generate_animal_badge_image,
    ],
    code_executor=sandbox_code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
