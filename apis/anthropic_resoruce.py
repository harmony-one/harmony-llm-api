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
        
        responseJson = extract_response_data(response)
    
    except anthropic.AnthropicError as e:
      app.logger.error(f"Anthropic API Error: {str(e)}")
      return jsonify({"error": str(e)}), 500
    except Exception as e:
      app.logger.error(f"Unexpected Error: {str(e)}")
      return jsonify({"error": "An unexpected error occurred."}), 500
    
    return responseJson, 200