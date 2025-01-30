import anthropic.types
from flask import request, Response, current_app as app
from flask_restx import Namespace, Resource
import anthropic
import json
from .auth import require_token
from res import EngMsg as msg, CustomError
from config import config
from services.telegram import telegram_report_error

api = Namespace('xai', description=msg.API_NAMESPACE_XAI_DESCRIPTION)

client = anthropic.Anthropic(
    base_url="https://api.x.ai",
    api_key=config.XAI_API_KEY, 
)

def data_generator(response):
    # input_token = 0
    # output_token = 0
    for event in response:
        if event.type == 'message_start':
            input_token = event.message.usage.input_tokens
        elif event.type == 'content_block_delta':
            text = event.delta.text
            yield f"{text}"
        elif event.type == 'message_delta':
            output_tokens = event.usage.output_tokens
    yield f"Input Token: {input_token}"
    yield f"Output Tokens: {output_tokens}"


def extract_response_data(response):
    return response.model_dump_json()


@api.route('/completions')
class XaiCompletionRes(Resource):
    
    @require_token
    def post(self):
        """
        Endpoint to handle xAI request.
        Receives a message from the user, processes it, and returns a response from the model.
        """
        app.logger.info('handling xAI request')
        data = request.json
        try:
            if data.get('stream') == "True":
                data['stream'] = True  # Convert stream to boolean
            messages = [{"content": m["content"], "role": m["role"]} for m in data.get('messages')]
            data['messages'] = messages
            response = client.messages.create(**data)
            if data.get('stream'):
                return Response(data_generator(response), mimetype='text/event-stream')

            # response = client.messages.create(**data)
            responseJson = extract_response_data(response)


        except anthropic.APIError as e:
            # This will catch BadRequestError, RateLimitError, AuthenticationError, etc.
            error_code = getattr(e, 'status_code', 500)
            error_message = str(e)
            app.logger.error(f"API Error: ({error_code}) {error_message}")
            telegram_report_error("xai", "NO_CHAT_ID", error_code, error_message)
            raise CustomError(error_code, error_message)
        
        except Exception as e:
            app.logger.error(f"Unexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")

        return responseJson, 200
