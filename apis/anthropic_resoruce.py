from flask import request, jsonify, Response, make_response, current_app as app
from flask_restx import Namespace, Resource
import anthropic
import json

from res import EngMsg as msg
from config import config

api = Namespace('anthropic', description=msg.API_NAMESPACE_OPENAI_DESCRIPTION)

client = anthropic.Anthropic(
  api_key=config.ANTHROPIC_API_KEY,
)

def data_generator(response):
    for chunk in response:
        yield f"data: {json.dumps(chunk)}\n\n"

def create_message_dict(response):
  content_blocks = [{
      'text': content_block.text,
      'type': content_block.type
  } for content_block in response.content]
  usage_dict = {
      'input_tokens': response.usage.input_tokens,
      'output_tokens': response.usage.output_tokens
  }
  message_dict = {
      'id': response.id,
      'model': response.model,
      'role': response.role,
      'stop_reason': response.stop_reason,
      'type': response.type,
      'usage': usage_dict,
      'content': content_blocks
  }
  return message_dict

@api.route('/completions') 
class AnthropicCompletionRes(Resource):
    
    def post(self):
        """
        Endpoint to handle Anthropic request.
        Receives a message from the user, processes it, and returns a response from the model.
        """ 
        app.logger.info('handling anthropic request')
        app.logger.info('Handling Anthropics API request')
    
        data = request.json
        try:
          if data.get('stream') == "True":
            data['stream'] = True  # Convert stream to boolean
                
          response = client.messages.create(**data)
          
          if data.get('stream'):
            return Response(data_generator(response), mimetype='text/event-stream')
          
          message_dict = create_message_dict(response)
          return jsonify(message_dict), 200
        except anthropic.AnthropicError as e:
          app.logger.error(f"Anthropic API Error: {str(e)}")
          return jsonify({"error": str(e)}), 500
        except Exception as e:
          app.logger.error(f"Unexpected Error: {str(e)}")
          return jsonify({"error": "An unexpected error occurred."}), 500
