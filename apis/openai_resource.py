import openai
import os

from flask import g, request, jsonify, make_response, current_app as app
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename
from openai.error import OpenAIError
from models.enums import ModelType
from .auth import require_any_auth, require_token
from res import EngMsg as msg, CustomError
from services import telegram_report_error
from services.payment import check_balance, llm_models_manager

api = Namespace('openai', description=msg.API_NAMESPACE_OPENAI_DESCRIPTION)

ALLOWED_EXTENSIONS = {'wav', 'm4a', 'mp3', 'mp4'}

def get_transcription(path):
    try:
        audio_file = open(path, 'rb')
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
        return response.text 
    except Exception as e:
        app.logger.error(f"Transcription error: {str(e)}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api.route('/upload-audio', methods=['POST'])
class UploadAudioFile(Resource):
    
    @api.doc(params={"data": msg.API_DOC_PARAMS_DATA})
    @require_token
    def post(self):
        """
        Endpoint to handle Openai's Whisper request.
        Receives an audio from the user, processes it, and returns a transcription.
        """
        app.logger.info('handling upload-audio request') 
        data = request.files
        try:
            if 'data' not in request.files:
                return make_response(jsonify({"error": 'No file part'})), 400
                
            file = data['data']
            if file.filename == '':
                return make_response(jsonify({"error": 'No selected file'})), 400
                
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                transcription = get_transcription(file_path)
                os.remove(file_path)
                
                if not transcription:
                    return make_response(jsonify({"error": 'Transcription failed'})), 500
                    
                return f"{transcription}", 200
            else:
                return make_response(jsonify({"error": 'Invalid file format'})), 400
                
        except OpenAIError as e:
            error_message = str(e)
            app.logger.error(f"OpenAI API Error: {error_message}")
            telegram_report_error("openai", "NO_CHAT_ID", e.code, error_message)
            raise CustomError(500, error_message)
        except Exception as e:
            error_message = str(e)
            app.logger.error(f"Unexpected Error: {error_message}")
            raise CustomError(500, "An unexpected error occurred.")

@api.route('/generate-image', methods=['POST'])
class GenerateImage(Resource):
    @require_any_auth
    @check_balance 
    def post(self):
        try:
            app.logger.info('handling generate-image request')
            data = request.get_json()
            if not data or 'prompt' not in data:
                return {"error": "No prompt provided"}, 400

            size = data.get('size', '1024x1024')
            n = min(max(1, data.get('n', 1)), 10)

            if g.is_jwt_user:
                transaction = llm_models_manager.record_transaction(
                    user_id=g.user.id,
                    model_version=ModelType.DALL_E,
                    tokens_input=n,
                    tokens_output=0,
                    endpoint='/generate-image',
                    status='processing',
                    amount=g.estimated_cost
                )

            response = openai.Image.create(
                prompt=data['prompt'],
                size=size,
                n=n,
            )

            return {"images": [img['url'] for img in response['data']]}, 200

        except OpenAIError as e:
            error_message = str(e)
            app.logger.error(f"OpenAI API Error: {error_message}")
            telegram_report_error("openai", "NO_CHAT_ID", e.code, error_message)
            raise CustomError(500, error_message)
        except Exception as e:
            error_message = str(e)
            app.logger.error(f"Unexpected Error: {error_message}")
            raise CustomError(500, "An unexpected error occurred.")