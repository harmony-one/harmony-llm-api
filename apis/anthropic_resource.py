from flask import request, jsonify, Response, make_response, abort, current_app as app
from flask_restx import Namespace, Resource
import anthropic
import json
import os
from res import EngMsg as msg, CustomError
from config import config
from pdfminer.high_level import extract_text
from services import PdfHandler
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


api = Namespace('anthropic', description=msg.API_NAMESPACE_OPENAI_DESCRIPTION)

client = anthropic.Anthropic(
    api_key=config.ANTHROPIC_API_KEY,
)
print(client.api_key)


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

def get_pdf_text(pdf):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = secure_filename(pdf.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pdf.save(file_path)
    pdf_file = open(file_path, 'rb')
    pdf_text = extract_text(pdf_file)
    return {
        "text": pdf_text,
        "path": file_path
    }


def create_message(text):
    return [
        {
            "role": "user",
            "content": [
                    {
                        "type": "text",
                        "text": text
                    }
            ]
        }
    ]


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

@api.route('/pdf/inquiry')
class AnthropicPDFSummary(Resource):

    @api.doc(params={"pdf": msg.API_DOC_PARAMS_PDF,
                    "url": msg.API_DOC_PARAMS_URL,
                    "model": msg.API_DOC_PARAMS_MODEL,
                    "maxTokens": msg.API_DOC_PARAMS_MAX_TOKENS,
                    "system": msg.API_DOC_PARAMS_SYSTEM})
    def post(self):
        """
        Endpoint to handle PDF parser and summary.
        """
        app.logger.info('handling pdf summary request')

        parser = api.parser()
        parser.add_argument('pdf', type=FileStorage, location='files')
        parser.add_argument('model', type=str)
        parser.add_argument('system', type=str)
        parser.add_argument('maxTokens', type=int)
        parser.add_argument('url', type=str)
        try:
            args = parser.parse_args()
            pdf_file = args.get('pdf', None)
            model = args.get('model', 'claude-3-opus-20240229')
            system = args.get('system', 'Summarize this text')
            max_tokens = args.get('maxTokens', 1000)
            url = args.get('url', None)
            if pdf_file:
                result = get_pdf_text(pdf_file)
                if (result.get('text')):
                    messages = create_message(result.get('text'))
                    fco = client.messages.create(
                        messages=messages, model=model, system=system, max_tokens=max_tokens)
                    print(fco)
                    data = {'message': msg.TEMP_PDF_INQUIRY_RESPONSE}
                    response = jsonify(data)
                    response.headers['Content-Type'] = 'application/json'
                    return response
            elif (url and url.lower().endswith('.pdf')):
                pdf_handler = PdfHandler()
                data = pdf_handler.get_pdf_from_url(url)
                pdf_text = extract_text(data)
                print(pdf_text)
                if (pdf_text):
                    messages = create_message(pdf_text)
                    # response = client.messages.create(
                    #     messages=messages, model=model, system=system, max_tokens=max_tokens)
                    data = {'message': msg.TEMP_PDF_INQUIRY_RESPONSE}
                    response = jsonify(data)
                    response.headers['Content-Type'] = 'application/json'
                    print('response', response)
                    return response
            else:
                raise CustomError(400, "Bad request")

        except anthropic.AnthropicError as e:
            error_code = e.status_code
            error_json = json.loads(e.response.text)
            error_message = error_json["error"]["message"]
            raise CustomError(error_code, error_message)
        except Exception as e:
            app.logger.error(f"Unexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")