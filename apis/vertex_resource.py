import os
from flask import g, request, Response, jsonify, make_response, current_app as app
from flask_restx import Namespace, Resource
from vertexai.language_models import ChatModel, ChatMessage
from vertexai.preview.generative_models import GenerativeModel
from vertexai.generative_models import ResponseValidationError
from google.api_core.exceptions import GoogleAPICallError, ClientError
import google.generativeai as genai
from google.cloud import aiplatform
from google.oauth2 import service_account
import vertexai
import json

from .auth import require_any_auth, require_token
from services import telegram_report_error
from services.payment import llm_models_manager
from res import EngMsg as msg, CustomError
from services.payment.decorators import check_balance

# Initialize Google Cloud credentials and services
with open("res/service_account.json") as f:
    service_account_info = json.load(f)
    project_id = service_account_info["project_id"]

my_credentials = service_account.Credentials.from_service_account_info(service_account_info)
aiplatform.init(credentials=my_credentials)
genai.configure(credentials=my_credentials)
vertexai.init(project=project_id, location="us-central1")

api = Namespace('vertex', description=msg.API_NAMESPACE_VERTEX_DESCRIPTION, path='/vertex')

def basic_data_generator(response):
    for event in response:
        yield f"Text: {event.text}"

def data_generator(response, input_token_count, model: GenerativeModel):
    completion = ""
    for chunk in response:
        if chunk is not None:
            try:
                if hasattr(chunk, 'text'):
                    completion += chunk.text + " "
                    yield f"{chunk.text}"
            except (ValueError, Exception):
                continue
                
    try:
        completion_tokens = model.count_tokens(completion)
        yield f"Input Token: {input_token_count}"
        yield f"Output Tokens: {completion_tokens.total_tokens}"
    except Exception:
        pass

@api.route('/completions')
class VertexCompletionRes(Resource):
    
    @require_token
    def post(self):
        """
        Endpoint to handle Google's Vertex/Palm2 LLMs.
        Receives a message from the user, processes it, and returns a response from the model.
        """
        app.logger.info('handling chat-bison request')
        data = request.json
        try:
            if data.get('stream') == "True":
                data['stream'] = True

            chat_model = ChatModel.from_pretrained("chat-bison@001")
            parameters = {
                "max_output_tokens": 800,
                "temperature": 0.2
            }
            
            prompt = data.get('messages')[-1]
            messages = data.get('messages')
            messages.pop()
            history = [ChatMessage(item.get('content'), item.get('author')) for item in messages]
            
            chat = chat_model.start_chat(
                max_output_tokens=800,
                message_history=history
            )
            response = chat.send_message(f"{prompt.get('content')}", **parameters)
            
            return make_response(jsonify(response), 200)
            
        except ResponseValidationError as e:
            telegram_report_error("vertex", "NO_CHAT_ID", "NO_CODE", str(e))
            raise CustomError(e.code, e.message)
        except GoogleAPICallError as e:
            telegram_report_error("vertex", "NO_CHAT_ID", e.code, e.message)
            raise CustomError(e.code, e.message)
        except ClientError as e:
            telegram_report_error("vertex", "NO_CHAT_ID", e.code, e.message)
            raise CustomError(e.code, e.message)
        except Exception as e:
            app.logger.error(f"Unexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")

@api.route('/completions/gemini')
class VertexGeminiCompletionRes(Resource):
    @require_any_auth
    @check_balance
    def post(self):
        """
        Endpoint to handle Google's Vertex/Gemini.
        Receives a message from the user, processes it, and returns a stream response from the model.
        """
        app.logger.info('handling gemini request')
        data = request.json
        try:
            if data.get('stream') == "True":
                data['stream'] = True
                
            model = data.get('model')
            system_instruction = data.get('system')
            max_output_tokens = data.get('max_tokens')
            
            generation_config = genai.GenerationConfig(
                max_output_tokens=int(max_output_tokens),
                temperature=0.1,
                top_p=1.0,
                top_k=40,
            )

            chat_model = genai.GenerativeModel(model, system_instruction=system_instruction)
            
            # Handle message format
            if all(
                isinstance(m, dict) and
                set(m.keys()) == {"parts", "role"} and
                isinstance(m["parts"], dict) and
                set(m["parts"].keys()) == {"text"} and
                m["role"] in ["model", "user"]
                for m in data.get('messages')
            ):
                messages = data.get('messages')
            else:
                messages = [
                    {"parts": {"text": m["content"]}, "role": "model" if m["role"] != "user" else "user"}
                    for m in data.get('messages')
                ]

            history = []
            for item in messages:
                if isinstance(item, dict) and 'parts' in item and isinstance(item['parts'], dict) and 'text' in item['parts']:
                    text = item['parts']['text']
                    role = item.get('role')
                    if text and role:
                        history.append({'role': role, 'parts': [text]})

            input_tokens = chat_model.count_tokens(history)
            
            if data['stream']:
                response = chat_model.generate_content(history, generation_config=generation_config, stream=True)
                
                if g.is_jwt_user:
                    llm_models_manager.record_transaction(
                        user_id=g.user.id,
                        model_version=model,
                        tokens_input=input_tokens.total_tokens,
                        tokens_output=0,
                        endpoint=request.path,
                        status='success',
                        amount=g.estimated_cost
                    )
                    
                return Response(data_generator(response, input_tokens.total_tokens, chat_model), mimetype='text/event-stream')
            else:
                response = chat_model.generate_content(history, generation_config=generation_config, stream=False)
                if g.is_jwt_user:
                    llm_models_manager.record_transaction(
                        user_id=g.user.id,
                        model_version=model,
                        tokens_input=input_tokens.total_tokens,
                        tokens_output=0,
                        endpoint=request.path,
                        status='success',
                        amount=g.estimated_cost
                    )
                return make_response(jsonify(response), 200)
                
        except ResponseValidationError as e:
            telegram_report_error("vertex", "NO_CHAT_ID", "NO_CODE", str(e))
            raise CustomError(e.code, e.message)
        except GoogleAPICallError as e:
            telegram_report_error("vertex", "NO_CHAT_ID", e.code, e.message)
            raise CustomError(e.code, e.message)
        except ClientError as e:
            telegram_report_error("vertex", "NO_CHAT_ID", e.code, e.message)
            raise CustomError(e.code, e.message)    
        except Exception as e:
            app.logger.error(f"Unexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")