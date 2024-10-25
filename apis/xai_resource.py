from flask import request, Response, current_app as app
from flask_restx import Namespace, Resource
import anthropic
import json
from res import EngMsg as msg, CustomError
from config import config

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

        except anthropic.AnthropicError as e:
            error_code = e.status_code
            error_json = json.loads(e.response.text)
            error_message = error_json["error"]["message"]
            app.logger.error(f"Unexpected Error: ({error_code}) {error_message}")
            raise CustomError(error_code, error_message)
        except Exception as e:
            app.logger.error(f"Unexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")

        return responseJson, 200
