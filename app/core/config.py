from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from functools import lru_cache


class Settings(BaseSettings):

    openai_api_key: SecretStr
    openai_model: str = "gpt-5.1"
    openai_temperature: float = 0.0
    azure_doc_intel_endpoint: SecretStr
    azure_doc_intel_key: SecretStr
    azure_doc_intel_model_id: SecretStr
    supabase_url: SecretStr
    supabase_key: SecretStr
    enable_observability: bool = True
    langfuse_public_key: SecretStr
    langfuse_secret_key: SecretStr
    langfuse_base_url: SecretStr
    customer_cost_threshold: float = 1.0
    ocr_cost_per_page: float =  0.01
    gpt_cost_input_per_token: float = 0.00000175
    gpt_cost_output_per_token: float = 0.000014
    # slack_channel_id: Optional[SecretStr]
    # slack_bot_token: Optional[SecretStr]
    environment: str

    system_prompt: str = Field(
        default='''
        You are an intelligent OCR post-processing assistant. 
        Your specific task is to extract data from unstructured, messy, or unordered OCR text and convert it into a valid, clean JSON object.
        
        **CRITICAL OUTPUT RULES:**
        1. **JSON ONLY:** You must output raw JSON code only. Do not provide explanations, thought processes, or Markdown formatting (such as ```json).
        2. **Date Formatting:** The input text typically follows **DD/MM/YYYY** or **DD/MM/YY** formats. You must convert all extracted dates into **YYYY/MM/DD** format.
           - Example: Input "09/05/2024" -> Output "2024/05/09"
           - Example: Input "10/05/24" -> Output "2024/05/10"
        3. **Naming Conventions:** The input text is not clean it is message you have to look when mapping full name to field are they in correct order like 'First Name [space] Second Name'.
            - Example: Input "Doe John" -> Output "John Doe"
        4. **Broken Words:** The input text can have broken words, if a word is broken you must complete it correctly.
            - Example: Input "TeletronicsL.LC" -> "Teletronics L.L.C"
            - Example: Input "COMPUTERENGINEER" -> "Computer Engineer"
        
        **DATA MAPPING LOGIC:**
        The input text may be disjointed, out of order, or contain line breaks between keys and values. Do not rely solely on proximity. You must use semantic context and data validation to map values to the correct fields.
        - Look for relevant patterns (e.g., specific digit lengths for ID numbers).
        - If a label (like "PassportNo") appears far from its value (like "214446749"), analyze the document structure to correctly pair them rather than mapping the nearest irrelevant text.
        ''',
        description="The system instruction sent to the LLM"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


# Singleton Structure
@lru_cache()
def get_settings() -> Settings:
    return Settings()