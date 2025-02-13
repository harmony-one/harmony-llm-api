from flask import request, Response, current_app as app
from flask_restx import Namespace, Resource
from openai import OpenAI
import json
from .auth import require_any_auth, require_token
from services import telegram_report_error
from res import EngMsg as msg, CustomError
from config import config

api = Namespace('deepseek', 'DeepSeek API') # description=msg.API_NAMESPACE_DEEPSEEK_DESCRIPTION)

print('FCO:::::::::::::', config.OPEN_ROUTER_DEEPSEEK_API_KEY) 

DEFAULT_HEADERS = {
    "HTTP-Referer": "https://harmony.one", 
    "X-Title": "Harmony LLM API",
}
# OPENAI_API_KEY
client = OpenAI(
    api_key=config.OPEN_ROUTER_DEEPSEEK_API_KEY,  
    base_url=config.OPEN_ROUTER_DEEPSEEK_BASE_URL,
    # default_headers=DEFAULT_HEADERS # required by Open ROUTER
)

def check_open_router_provider():
    return client.base_url.host.find('openrouter') != -1

def get_model_by_provider(model):
    if check_open_router_provider():
        if model.find('chat') != -1:
            return f"deepseek/deepseek-r1:free"
    return model

def data_generator(response):
    prompt_tokens = 0
    completion_tokens = 0
    try:
        for chunk in response:
            if hasattr(chunk, 'usage') and chunk.usage is not None:
                usage = dict(chunk.usage)
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
            elif (hasattr(chunk, 'choices') and 
                  chunk.choices and 
                  hasattr(chunk.choices[0], 'delta') and 
                  hasattr(chunk.choices[0].delta, 'content') and 
                  chunk.choices[0].delta.content is not None):
                content = chunk.choices[0].delta.content
                if content.strip(): 
                    yield content
        
        if prompt_tokens or completion_tokens:
            yield f"Input Tokens: {prompt_tokens}"
            yield f"Output Tokens: {completion_tokens}"
            # yield f"\nInput Tokens: {prompt_tokens}\nOutput Tokens: {completion_tokens}"
    except Exception as e:
        app.logger.error(f"Streaming error: {str(e)}")
        yield f"Error: {str(e)}"

@api.route('/completions')
class DeepSeekCompletionRes(Resource):
    
    @require_token 
    def post(self):
        """
        Endpoint to handle DeepSeek chat completion requests.
        Receives a message from the user, processes it, and returns a response from the model.
        """
        app.logger.info('handling deepseek request')
        data = request.json
        try:
            # Convert stream parameter if present
            if data.get('stream') == "True":
                data['stream'] = True
            elif data.get('stream') == "False":
                data['stream'] = False

            # Extract messages from the request
            messages = [{"content": m["content"], "role": m["role"]} for m in data.get('messages', [])]
            model = get_model_by_provider(data.get('model', 'deepseek-chat'))
            # Prepare the completion request
            completion_args = {
                "model": model,
                "messages": messages,
                "stream": data.get('stream', False)
            }
            # Add optional parameters if they exist in the request
            if 'temperature' in data:
                completion_args['temperature'] = float(data['temperature'])
            if 'max_tokens' in data:
                completion_args['max_tokens'] = int(data['max_tokens'])
            if data.get('stream'):
                completion_args['stream_options']={"include_usage": True}
            if check_open_router_provider():
                completion_args['extra_headers'] = {
                "HTTP-Referer": "https://harmony.one", 
                "X-Title": "Harmony Llm Api",
            }
            response = client.chat.completions.create(**completion_args)
            
            # Handle streaming response
            if data.get('stream'):
                return Response(data_generator(response), mimetype='text/event-stream')
            # Handle regular response
            return response.model_dump(), 200

        except Exception as e:
            error_code = getattr(e, 'status_code', 500)
            error_message = str(e)
            app.logger.error(f"API Error: ({error_code}) {error_message}")
            telegram_report_error("deepseek", "NO_CHAT_ID", error_code, error_message)
            raise CustomError(error_code, error_message)