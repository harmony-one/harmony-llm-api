from flask import request, Response, jsonify, make_response, current_app as app
from flask_restx import Namespace, Resource
from vertexai.language_models import ChatModel, ChatMessage
from vertexai.preview.generative_models import GenerativeModel, Content, Part
import google.generativeai as genai
from google.generativeai.types import content_types
from google.oauth2 import service_account
import google.cloud.aiplatform as aiplatform
# from litellm import litellm
import openai
import vertexai
import json

from res import EngMsg as msg, CustomError

with open(
    "res/service_account.json"
) as f:
    service_account_info = json.load(f)

my_credentials = service_account.Credentials.from_service_account_info(
    service_account_info
)

aiplatform.init(
    credentials=my_credentials,
)

with open("res/service_account.json", encoding="utf-8") as f:
    project_json = json.load(f)
    project_id = project_json["project_id"]


# litellm.vertex_project = project_id
# litellm.vertex_location = "us-central1"

genai.configure(credentials=my_credentials) # (project_id=project_id, location='us-central')
vertexai.init(project=project_id, location="us-central1")

api = Namespace('vertex', description=msg.API_NAMESPACE_VERTEX_DESCRIPTION)


def basic_data_generator(response):
    for event in response:
        yield f"Text: {event.text}"

def data_generator(response, input_token_count, model: GenerativeModel):
    completion = ""
    for event in response:
        completion += event.text + " "
        yield f"{event.text}"
    completionTokens = model.count_tokens(completion)
    yield f"Input Token: {input_token_count}"
    yield f"Output Tokens: {completionTokens.total_tokens}"

@api.route('/completions')
class VertexCompletionRes(Resource):

    def post(self):
        """
        Endpoint to handle Google's Vertex/Palm2 LLMs.
        Receives a message from the user, processes it, and returns a response from the model.
        """
        app.logger.info('handling chat-bison request')
        data = request.json
        if data.get('stream') == "True":
            data['stream'] = True  # convert to boolean
        try:
            if data.get('stream') == "True":
                data['stream'] = True  # convert to boolean
            # pass in data to completion function, unpack data

            chat_model = ChatModel.from_pretrained("chat-bison@001")
            parameters = {
                "max_output_tokens": 800,
                "temperature": 0.2
            }
            prompt = data.get('messages')[-1]
            messages = data.get('messages')
            messages.pop()
            history = [ChatMessage(item.get('content'), item.get(
                'author')) for item in messages]
            chat = chat_model.start_chat(
                max_output_tokens=800,
                message_history=history
            )
            response = chat.send_message(
                f"{prompt.get('content')}", **parameters)
            # if data['stream'] == True: # use generate_responses to stream responses
            #     return Response(data_generator(response), mimetype='text/event-stream')

            # return f"{response}", 200 # non streaming responses
            return make_response(jsonify(response), 200)
        except openai.error.OpenAIError as e:
            # Handle OpenAI API errors
            error_message = str(e)
            app.logger.error(f"OpenAI API Error: {error_message}")
            raise CustomError(500, error_message)
        except Exception as e:
            # Handle other unexpected errors
            error_message = str(e)
            app.logger.error(f"Unexpected Error: {error_message}")
            raise CustomError(500, "An unexpected error occurred.")


@api.route('/completions/gemini')
class VertexGeminiCompletionRes(Resource):

    def post(self):
        """
        Endpoint to handle Google's Vertex/Gemini.
        Receives a message from the user, processes it, and returns a stream response from the model.
        """
        app.logger.info('handling gemini request')
        data = request.json
        try:
            if data.get('stream') == "True":
                data['stream'] = True  # convert to boolean
            model = data.get('model')
            print(model)
            chat_model = genai.GenerativeModel(model)
            print("MODEL", chat_model._model_name)
            parameters = {
                "max_output_tokens": 800,
                "temperature": 0.1,
                "top_p": 1.0,
                "top_k": 40,
            }
            messages = data.get('messages')
            history = []
            for item in messages:
                if isinstance(item, dict) and 'parts' in item and isinstance(item['parts'], dict) and 'text' in item['parts']:
                    text = item['parts']['text']
                    role = item.get('role')
                    if text and role:
                        temp_content = {'role':role, 'parts': [text]}
                        history.append(temp_content)
                else:
                    print("Skipping item - Invalid format:", item)
            inputTokens = chat_model.count_tokens(history)
            if data['stream'] == True: # use generate_responses to stream responses
                response = chat_model.generate_content(history, stream=True)
                return Response(data_generator(response, inputTokens.total_tokens, chat_model), mimetype='text/event-stream')
            
            return make_response(jsonify(response), 200)
        except openai.error.OpenAIError as e:
            # Handle OpenAI API errors
            error_message = str(e)
            app.logger.error(f"OpenAI API Error: {error_message}")
            raise CustomError(500, error_message)
        except Exception as e:
            # Handle other unexpected errors
            error_message = str(e)
            app.logger.error(f"Unexpected Error: {error_message}")
            raise CustomError(500, "An unexpected error occurred.")
