from langfuse import observe as _langfuse_observe, Langfuse
from langfuse.openai import AsyncOpenAI as LangfuseAsyncOpenAI
from openai import AsyncOpenAI as StandardAsyncOpenAI
from app.core import get_settings
from typing import Union
from functools import lru_cache


@lru_cache()
def get_langfuse():
    return Langfuse(
        public_key=get_settings().langfuse_public_key.get_secret_value(),
        secret_key=get_settings().langfuse_secret_key.get_secret_value(),
        host=get_settings().langfuse_base_url.get_secret_value(),
        tracing_enabled=get_settings().enable_observability,
        environment=get_settings().environment,
    )

def observe(*args, **kwargs):
    """
    A custom wrapper around Langfuse.
    If Langfuse is disabled in config, this does nothing (no-op).
    If enabled, it passes the call through to Langfuse.
    """
    get_langfuse()

    def decorator(func):
        # Check config to see if we should actually track this
        # This prevents errors in Local/Test environments where keys might be missing
        if not get_settings().enable_observability:
            return func  # Return the original function untouched (No overhead)

        # If enabled, verify if we need to call the real decorator
        # (Handling the edge case where @observe is used with or without parens)
        if _langfuse_observe:
            wrapped_func = _langfuse_observe(*args, **kwargs)(func)
            return wrapped_func

        return func

    return decorator


def get_llm_client() -> Union[LangfuseAsyncOpenAI, StandardAsyncOpenAI]:
    """
    Returns an instrumented Client if observability is enabled.
    Otherwise, returns a standard OpenAI client (zero overhead).
    """
    api_key = get_settings().openai_api_key.get_secret_value()

    if get_settings().enable_observability:
        return LangfuseAsyncOpenAI(
            api_key=api_key,
        )
    else:
        return StandardAsyncOpenAI(
            api_key=api_key
        )


def calculate_azure_costing(pages: int):
    """
    Updates the current active span with Azure OCR usage data.
    Must be called inside a function decorated with @observe.
    """
    if not get_settings().enable_observability:
        return

    # 2. Update the CURRENT span
    get_langfuse().update_current_generation(
        model="azure-ocr-prebuilt-read",
        usage_details={
            "input": pages,
        },
        metadata={
            "usage_unit": "PAGES"
        }
    )