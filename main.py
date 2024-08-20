import asyncio
import base64
import functools
import os
import traceback
from io import BytesIO

import requests
from PIL import Image
from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()

# These example values won't work. You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
api_id = os.environ["API_ID"]
bot_token = os.environ["BOT_TOKEN"]
api_hash = os.environ["API_HASH"]
rapidapi_key = os.environ["RAPIDAPI_KEY"]

client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)


def save_img(user_id, img_url):
    resp = requests.get(img_url, stream=True)
    image_name = f"temp_{user_id}.jpg"
    image_path = f"./temp/{image_name}"
    with open(image_path, "wb") as f:
        f.write(resp.content)
    return image_path


def convert_to_base64(image_path):
    image = Image.open(image_path)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return b64_img


def call_machaao_rapidapi(user_id, text, image_str):
    output = {
        "text": None,
        "image": None
    }

    url = "https://messengerx-io.p.rapidapi.com/process/jeanie"

    payload = {
        "message_data": {
            "text": f"{text}"
        }
    }

    if image_str:
        payload["message_data"]["attachment"] = {
            "type": "image/jpeg",
            "raw": f"data:image/jpeg;base64,{image_str}"
        }

    headers = {
        "x-rapidapi-key": f"{rapidapi_key}",
        "x-rapidapi-host": "messengerx-io.p.rapidapi.com",
        "Content-Type": "application/json",
        "X-Sender-Id": f"{user_id}"
    }

    response = requests.post(url, json=payload, headers=headers)
    resp = response.json()
    text = resp["output"]["output"]
    url_prefix = "https://ganglia.machaao.com/download"
    if url_prefix in text:
        url_start = text.find(url_prefix)
        url = text[url_start:]
        text = text[:url_start]
        output["image"] = url
        output["text"] = text
    else:
        output["text"] = text
    return output


save_path = "downloads/"


# Define the main chatbot handler
@client.on(events.NewMessage())
async def handle_start_command(event):
    SENDER = await event.get_sender()
    try:
        base64_image = None
        if event.photo:
            if event.message.message:
                user_input = event.message.message
            else:
                user_input = "Describe this image"
            saved_path = await event.download_media(save_path)
            base64_image = convert_to_base64(saved_path)
        else:
            user_input = event.message.message
        # user_id, text, image_url
        print(f"{SENDER.id}-> Message: {user_input}")
        history = [{"role": "user", "content": user_input}]
        loop = asyncio.get_running_loop()
        async with client.action(event.chat_id, 'typing'):
            resp = await loop.run_in_executor(
                None,
                functools.partial(
                    call_machaao_rapidapi,
                    user_id=SENDER.id,
                    text=user_input,
                    image_str=base64_image
                )
            )
        if resp.get("image") is None:
            text = resp["text"]
            history.append({"role": "assistant", "content": text})
            await client.send_message(SENDER, text, parse_mode='Markdown')
        else:
            image_url = resp["image"]
            text = resp["text"]
            img_path = save_img(SENDER.id, image_url)
            await client.send_file(SENDER, file=img_path, caption=text)
            os.remove(img_path)
    except Exception as e:
        print(traceback.format_exc())
        error_msg = "Something went wrong. Please try again."
        await client.send_message(SENDER, error_msg, parse_mode='Markdown')
    return


# Main function
if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    print("Bot Started...")
    client.run_until_disconnected()  # Start the bot!
