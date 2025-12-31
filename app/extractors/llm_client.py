import logging
from functools import lru_cache
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from openai import AsyncOpenAI

from app.core import get_settings, get_llm_client
from .prompt import get_prompt
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

T = TypeVar("T", bound=BaseModel)

def _require_dependencies() -> None:
    if AsyncOpenAI is None:
        raise RuntimeError(
            "openai package is not installed. Install it with `pip install openai` to use LLM extraction."
        )


@lru_cache(maxsize=1)
def _client() -> AsyncOpenAI:
    _require_dependencies()
    return get_llm_client()


def _render_prompt(doc_type: str, text: str, comments: Optional[str] = None) -> str:
    return get_prompt(doc_type).format(document_text=text.strip(), comments=comments)


async def extract_with_llm(
    doc_type: str, text: str, model_cls: Type[T], temperature: Optional[float] = None, comments: Optional[str] = None
) -> tuple[T, dict]:
    if not text.strip():
        raise ValueError("Document text is empty; OCR likely failed.")

    effective_temperature = get_settings().openai_temperature if temperature is None else temperature

    prompt = _render_prompt(doc_type, text, comments)
    messages = [
        ChatCompletionSystemMessageParam(role="system", content=get_settings().system_prompt),
        ChatCompletionUserMessageParam(role="user", content=prompt),
    ]

    request_kwargs = {
        "model": get_settings().openai_model,
        "messages": messages,
        "temperature": effective_temperature,
        "response_format": model_cls,
    }

    if get_settings().enable_observability:
        request_kwargs["name"] = "LLM"

    response = await _client().beta.chat.completions.parse(**request_kwargs)
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens
    }

    # This pulls the pre-validated Pydantic object
    data = response.choices[0].message.parsed
    # Optional: Check if it actually returned data (rare cases where it might be None)
    if not data:
        raise ValueError("The model failed to return structured data.")

    return data, usage
