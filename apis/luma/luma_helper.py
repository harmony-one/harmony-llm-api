import json
import time
from . import luna_client
import requests
from config import config


def send_telegram_message_with_download_button(chat_id, text, video_path):
    try:
        bot_token = config.TELEGRAM_API_KEY
        base_url = f"https://api.telegram.org/bot{bot_token}/"
        
        # Create inline keyboard
        keyboard = {
            "inline_keyboard": [[{
                "text": "Download Video",
                "callback_data": f"luma_dl:b50b566e-214f-46f6-9553-60a3bb8b076d" #{video_path}"
            }]]
        }
        
        params = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": json.dumps(keyboard)
        }
        
        response = requests.post(base_url + "sendMessage", json=params)

        return response.json()
    except Exception as e:
        print(e) 


def send_telegram_message(chat_id, text, video_url):
    bot_token = config.TELEGRAM_API_KEY
    base_url = f"https://api.telegram.org/bot{bot_token}/"
    
    # Create inline keyboard
    keyboard = {
        "inline_keyboard": [[{
            "text": "Download Video",
            "url": video_url
        }]]
    }
    
    params = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": json.dumps(keyboard)
    }
    
    response = requests.post(base_url + "sendMessage", json=params)
    return response.json()


def count_generation_states(generation_list):
    state_counts = {}

    for generation in generation_list.generations:
        state = generation.state
        state_counts[state] = state_counts.get(state, 0) + 1
  
    return {
        'state_counts': state_counts
    }

def count_generation_in_progress(generation_list):
    in_progress_count = 0

    for generation in generation_list.generations:
        state = generation.state        
        if state == 'dreaming':
            in_progress_count += 1

    return in_progress_count

def get_queue_time(in_progress_count):
    return in_progress_count * 60 # 60 secs per video

def process_generation(prompt, generation_id, chat_id):
    try:
        completed = False
        while not completed:
            generation = luna_client.generations.get(id=generation_id)
            if generation.state == "completed":
                completed = True
            elif generation.state == "failed":
                raise RuntimeError(f"Generation failed: {generation.failure_reason}")
            # time.sleep(30)  # Check every 30 seconds to reduce API calls
        
        video_url = generation.assets.video
        
        # Send Telegram message with download button
        message_text = f"Your Luma AI generation is complete!\nPrompt: {prompt}"

        send_telegram_message_with_download_button(chat_id, message_text, video_url)
        
        print(f"Generation {generation_id} completed and notified via Telegram")
    except Exception as e:
        error_message = f"Error processing generation {generation_id}: {str(e)}"
        print(error_message)
        print(chat_id, error_message, None)
        # send_telegram_message(chat_id, error_message, None)
