import requests
from urllib import request
from django.conf import settings

# ask_gpt collect your info and perform request to pota-api, make sure to catch any exception.
def ask_gpt(user_email: str, reset_token: str, prompt: str, chat_id: str) -> str:

    headers = {
        "Content-Type": "application/json",
        settings.POTA_TOKEN_HEADER : reset_token
    }

    data = {
        "email": user_email,
        "prompt": prompt,
    }

    if chat_id is not None:
        data["chat_id"] = chat_id

    gpt_resp = request.post(
        url=settings.POTA_API_URI,
        headers=headers,
        json=data
    )
    parsed_resp = gpt_resp.json()

    if not gpt_resp.ok:
        raise requests.exceptions.RequestException(parsed_resp.get("detail"))

    return parsed_resp.get("message")
            