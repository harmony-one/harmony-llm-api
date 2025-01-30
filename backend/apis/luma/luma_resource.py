import concurrent.futures
import lumaai

from flask import request, jsonify, Response, make_response, abort, current_app as app
from flask_restx import Namespace, Resource

from ..auth import require_token
from . import luna_client
from .luma_helper import count_generation_in_progress, count_generation_states, get_queue_time, process_generation, LumaErrorHandler
from res import EngMsg as msg, CustomError
from config import config
from services import telegram_report_error

api = Namespace('luma', description=msg.API_NAMESPACE_ANTHROPIC_DESCRIPTION)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS)

class Generation:
    def __init__(self, id):
        self.id = id


@api.route('/generations')
class LumaAiGenerationRes(Resource):
    
    @require_token
    def post(self):
        """
        Endpoint to handle Luma requests.
        Receives the prompt, start procesing it, and returns the generations's id, and generation in progress queue.
        """
        app.logger.info('handling luma requests')
        data = request.json
        prompt = data.get('prompt')
        chat_id = data.get('chat_id')
        try:
            if not prompt or not chat_id:
                return {'error': 'Both prompt and chat_id are required'}, 400
            # generation = Generation(id="b50b566e-214f-46f6-9553-60a3bb8b076d")
            generation = luna_client.generations.create(prompt=prompt) #Generation(id="b50b566e-214f-46f6-9553-60a3bb8b076d")
            ## generation = Generation(id="0da62dac-f11f-4c47-0d7c-85324484c6bf")
            generation_list = luna_client.generations.list(limit=100, offset=0)
            in_progress = count_generation_in_progress(generation_list)
            queue_time = get_queue_time(in_progress)
            app.logger.info(f'Processing generation {generation.id} | generations in queue {in_progress}' )
            executor.submit(process_generation, prompt, generation.id, chat_id)
            return make_response(jsonify({"generation_id": f"{generation.id}", "in_progress": f"{in_progress}", "queue_time": f"{queue_time}"}), 200)
       
        except lumaai.APIError as e:
            status_code, error_detail = LumaErrorHandler.get_error_info(e)
            LumaErrorHandler.log_error(app.logger, e)
            telegram_report_error("luma", chat_id, status_code, error_detail)
            raise CustomError(status_code, error_detail)
    
        except Exception as e:
            app.logger.error(f"Unexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")

@api.route('/generations/list')
class LumaAiGenerationListRes(Resource):
    
    @require_token
    def get(self):
        """
        Endpoint that returns the counts of different generation's states.
        """
        app.logger.info('handling luma requests')
        generation_list = luna_client.generations.list(limit=100, offset=0)
        generations = count_generation_states(generation_list)
        return make_response(jsonify(generations), 200)


@api.route('/generations/<generation_id>')
class GenerationRes(Resource):
    
    @api.doc(params={"generation_id": msg.API_DOC_PARAMS_COLLECTION_NAME})
    @require_token
    def delete(self, generation_id):
        """
        Endpoint that deletes a generation
        """
        try:
            if (generation_id):
                luna_client.generations.delete(id=generation_id)
                return 'OK', 204
            else:
                return "Bad request, parameters missing", 400
        
        except lumaai.APIError as e:
            status_code, error_detail = LumaErrorHandler.get_error_info(e)
            LumaErrorHandler.log_error(app.logger, e)
            raise CustomError(status_code, error_detail)
        
        except Exception as e:
            error_message = str(e)
            app.logger.error(f"Unexpected Error: {error_message}")
            raise CustomError(500, "An unexpected error occurred.")
                


