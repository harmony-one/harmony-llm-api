from flask import request, jsonify, Response, make_response, current_app as app

from .vertex_resource import VertexGeminiCompletionRes
from .anthropic import AnthropicCompletionRes
from flask_restx import Namespace, Resource
from litellm import completion
from openai.error import OpenAIError
import json

from res import EngMsg as msg, CustomError

api = Namespace('llms', description=msg.API_NAMESPACE_LLMS_DESCRIPTION)

def data_generator(response):
    for chunk in response:
        yield f"data: {json.dumps(chunk)}\n\n"

@api.route('/completions/j2') 
class LlmsCompletionJ2Res(Resource):
    
    def post(self):
        """
        Endpoint to handle LLMs request.
        Receives a message from the user, processes it, and returns a response from the model.
        """ 
        app.logger.info('handling j2 request')
        data = request.json
        try:
            if data.get('stream') == "True":
                data['stream'] = True # convert to boolean
            # pass in data to completion function, unpack data
            response = completion(**data)
            if data['stream'] == True: 
                return Response(data_generator(response), mimetype='text/event-stream')
        except OpenAIError as e:
            # Handle OpenAI API errors
            error_message = str(e)
            app.logger.error(f"OpenAI API Error: {error_message}")
            raise CustomError(500, f"OpenAI API Error: {error_message}")
        except Exception as e:
            # Handle other unexpected errors
            error_message = str(e)
            app.logger.error(f"Unexpected Error: {error_message}")
            raise CustomError(500, f"An unexpected error occurred.")
        # return response, 200
        return make_response(jsonify(response), 200)


@api.route('/completions') 
class LlmsCompletionRes(Resource):
    
    def post(self):
        """
        Main Endpoint to handle Vertex and Anthropic request.
        Receives a message from the user, checks the model and redirects the request to the respective handler.
        """ 
        data = request.json
        model = data.get('model')

        if model.startswith('claude'):
            return AnthropicCompletionRes().post()
        elif model.startswith('gemini'):
            return VertexGeminiCompletionRes().post()
        else:
            # Handle unsupported models
            raise CustomError(400, "Unsupported model")