import copy
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from functools import lru_cache
from app.core import get_settings

bot_message_template = [
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "Cost Alert",
            "emoji": True
        },
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Placeholder"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Trace",
                "emoji": True
            },
            "value": "click_me_123",
            "style": "danger",
            "action_id": "traces_button_click"
        }
    }
]

@lru_cache(maxsize=1)
def _get_slack_client() -> WebClient:
    return WebClient(get_settings().slack_bot_token.get_secret_value())

async def slack_post_message(trace_link: str, msg: str):
    """
    Sends a structured Slack message with a trace button.
    :param trace_link: The URL for the button.
    :param msg: The main text content (Markdown).
    """
    try:
        # 1. Deep copy to ensure thread safety
        current_blocks = copy.deepcopy(bot_message_template)

        # 2. Add the italic instruction below the main message
        # Slack uses _text_ for italics
        full_message = f"{msg}\n\n_See complete trace by clicking on the button_"
        current_blocks[1]["text"]["text"] = full_message

        # 3. Inject the Trace URL into the button
        current_blocks[1]["accessory"]["url"] = trace_link

        # 4. Send the message
        _get_slack_client().chat_postMessage(
            channel=get_settings().slack_channel_id.get_secret_value(),
            blocks=current_blocks,
        )
    except SlackApiError as e:
        return