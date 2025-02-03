from flask import request, Response, current_app as app
from flask_restx import Namespace, Resource
from openai import OpenAI
import json
from .auth import require_any_auth, require_token
from services import telegram_report_error
from res import EngMsg as msg, CustomError
from config import config

api = Namespace('deepseek', description=msg.API_NAMESPACE_DEEPSEEK_DESCRIPTION)

client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,  # You'll need to add this to your config
    base_url="https://api.deepseek.com"
)

def data_generator(response):
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield f"{chunk.choices[0].delta.content}"

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
            
            # Prepare the completion request
            completion_args = {
                "model": data.get('model', 'deepseek-chat'),
                "messages": messages,
                "stream": data.get('stream', False)
            }

            # Add optional parameters if they exist in the request
            if 'temperature' in data:
                completion_args['temperature'] = float(data['temperature'])
            if 'max_tokens' in data:
                completion_args['max_tokens'] = int(data['max_tokens'])

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