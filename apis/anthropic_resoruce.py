from flask import request, jsonify, Response, make_response, abort, current_app as app
from flask_restx import Namespace, Resource
import anthropic
import json

from res import EngMsg as msg, CustomError
from config import config

api = Namespace('anthropic', description=msg.API_NAMESPACE_OPENAI_DESCRIPTION)

client = anthropic.Anthropic(
  api_key=config.ANTHROPIC_API_KEY,
)

def custom_serializer(obj):
    if obj.type != 'message_start':
        return obj.__dict__
    return obj

def data_generator(response):
    for event in response:
        if event.type == 'message_start':
            input_token = event.message.usage.input_tokens
            yield f"Input Token: {input_token}"
        elif event.type == 'content_block_delta':
            text = event.delta.text
            yield f"Text: {text}"
        elif event.type == 'message_delta':
            output_tokens = event.usage.output_tokens
            yield f"Output Tokens: {output_tokens}"

def extract_response_data(response):
    return response.model_dump_json()

@api.route('/completions') 
class AnthropicCompletionRes(Resource):
    
  def post(self):
    """
    Endpoint to handle Anthropic request.
    Receives a message from the user, processes it, and returns a response from the model.
    """ 
    app.logger.info('handling anthropic request')
    data = request.json
    try:
        if data.get('stream') == "True":
            data['stream'] = True  # Convert stream to boolean

        response = client.messages.create(**data)

        if data.get('stream'):
            return Response(data_generator(response), mimetype='text/event-stream')
        
        # response = client.messages.create(**data)
        responseJson = extract_response_data(response)
    
    except anthropic.AnthropicError as e:
        error_code = e.status_code
        error_json = json.loads(e.response.text)
        error_message = error_json["error"]["message"]
        raise CustomError(error_code, error_message)
    except Exception as e:
        app.logger.error(f"Unexpected Error: {str(e)}")
        raise CustomError(500, "An unexpected error occurred.")
    
    return responseJson, 200
  