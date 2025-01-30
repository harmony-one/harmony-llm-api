import json
import time
import lumaai
import requests
from lumaai import APIError
import lumaai
from config import config
from . import luna_client
import json
from services import send_telegram_error_message

def send_telegram_message_with_download_button(chat_id, text, generation_id):
    try:
        bot_token = config.TELEGRAM_API_KEY
        base_url = f"https://api.telegram.org/bot{bot_token}/"
        
        # Create inline keyboard
        keyboard = {
            "inline_keyboard": [[{
                "text": "Download Video",
                "callback_data": f"luma_dl:{generation_id}" #"luma_dl:b50b566e-214f-46f6-9553-60a3bb8b076d" #{video_path}"
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
    return in_progress_count * 45 # 45 secs per video

def process_generation(prompt, generation_id, chat_id):
    try:
        completed = False
        first_iteration = True
        while not completed:
            generation = luna_client.generations.get(id=generation_id)
            if generation.state == "completed":
                completed = True
            elif generation.state == "failed":
                raise RuntimeError(f"Generation failed: {generation.failure_reason}")
            else:
                if first_iteration: 
                    first_iteration = False
                    time.sleep(30)  # Check the first time 30 seconds to reduce API calls
                else:
                    time.sleep(15)  # Check every 15 seconds to reduce API calls
        
        # Send Telegram message with download button
        message_text = f"Your Luma AI generation is complete!\nPrompt: {prompt}"

        send_telegram_message_with_download_button(chat_id, message_text, generation_id)
        
        print(f"Generation {generation_id} completed and notified via Telegram")
    
    except lumaai.APIError as e: 
        error_detail = e.body.get('detail', 'Error processing the generation')
        print(f"Error processing the generation id ({generation_id}) for chat id ({chat_id}): {error_detail}")
        send_telegram_error_message(chat_id, f"Error processing the generation: {error_detail}")
        
class LumaErrorHandler:
    ERROR_MAPPING = {
        lumaai.BadRequestError: 400,
        lumaai.AuthenticationError: 401,
        lumaai.PermissionDeniedError: 403,
        lumaai.NotFoundError: 404,
        lumaai.UnprocessableEntityError: 422,
        lumaai.RateLimitError: 429,
        lumaai.APIConnectionError: 503,
    }

    @staticmethod
    def get_error_info(error: APIError):
        """
        Get the appropriate status code and error detail for a Luma API error.
        """
        error_class = error.__class__
        status_code = LumaErrorHandler.ERROR_MAPPING.get(error_class, 500)
        error_detail = error.body.get('detail', str(error))
        return status_code, error_detail

    @staticmethod
    def log_error(logger, error: APIError):
        """
        Log the error with appropriate details.
        """
        status_code, error_detail = LumaErrorHandler.get_error_info(error)
        logger.error(f"{error.__class__.__name__} (Status {status_code}): {error_detail}")