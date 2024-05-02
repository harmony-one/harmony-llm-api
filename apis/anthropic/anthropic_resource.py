import threading
from anthropic.types.beta.tools import ToolParam, ToolsBetaMessageParam
from uuid import uuid4
from flask import request, jsonify, Response, make_response, abort, current_app as app
from flask_restx import Namespace, Resource
import anthropic
import json
import os
from .anthropic_helper import anthropicHelper as helper
from app_types import ToolsBetaMessage
from res import EngMsg as msg, CustomError
from config import config
from pdfminer.high_level import extract_text
from services import PdfHandler
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

api = Namespace('anthropic', description=msg.API_NAMESPACE_ANTHROPIC_DESCRIPTION)

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=config.ANTHROPIC_API_KEY, 
)

parser = api.parser()
parser.add_argument('pdf', type=FileStorage, location='files')
parser.add_argument('model', type=str)
parser.add_argument('system', type=str)
parser.add_argument('maxTokens', type=int)
parser.add_argument('url', type=str)
parser.add_argument('jobDescription', type=str)

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
            yield f"{text}"
        elif event.type == 'message_delta':
            output_tokens = event.usage.output_tokens
            yield f"Output Tokens: {output_tokens}"


def extract_tool_response_data(message):

    betaMessage = ToolsBetaMessage(
        id=message.id,
        content=message.content,
        model=message.model,
        role=message.role,
        stop_reason=message.stop_reason,
        stop_sequence=message.stop_sequence,
        type= message.type,
        usage=message.usage)
    
    return json.dumps(betaMessage.to_dict())

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
        print(request.headers)
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

@api.route('/completions/tools')
class AnthropicCompletionToolRes(Resource):

    runningTools = []
    tools = helper.get_claude_tools_definition()

    def post(self):
        """
        Endpoint to handle Anthropic requests with Tools.
        Receives a message from the user and creates a tool handler.
        Returns a tool execution ID
        """
        app.logger.info('handling anthropic request')
        data = request.json
        try:
            if data.get('stream') == "True":
                data['stream'] = True  # Convert stream to boolean
            
            tool_execution_id = uuid4().hex
            helper.add_running_tool(tool_execution_id)
            thread = threading.Thread(target=self.__tool_request_handler, args=(data, tool_execution_id, app.app_context()))
            thread.start()
            return make_response(jsonify({"id": f"{tool_execution_id}"}), 200)
            
        except anthropic.AnthropicError as e:
            print('ERROR', e)
            error_code = e.status_code
            error_json = json.loads(e.response.text)
            error_message = error_json["error"]["message"]
            raise CustomError(error_code, error_message)
        except Exception as e:
            app.logger.error(f"Ucnexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")
        
    def __tool_request_handler(self, data, tool_execution_id, context):
        context.push()
        try:
            model = data.get('model')
            system = data.get('system')
            max_tokens = data.get('max_tokens')
            messages = data.get('messages')
            response = client.beta.tools.messages.create(
                model=model,
                max_tokens=1024,
                messages=messages,
                tools=self.tools,
            )
            
            if (response.stop_reason == "tool_use"):
                while (response.stop_reason == "tool_use"): 
                    messages.append({"role": response.role, "content": response.content})
                    tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
                    print('Tool use blocks size', len(tool_use_blocks))
                    
                    if (len(tool_use_blocks) > 1):
                        content = []
                        for block in tool_use_blocks:
                            tool_name = block.name
                            tool_input = block.input
                            print(f"\nTool Used: {tool_name}")
                            print(f"Tool Input: {tool_input}")

                            tool = helper.excecute_tool(tool_name)
                            if (tool):
                                info = tool.run(tool_input)
                            else:
                                info = "no data available"
                            content.append({
                                    'type': 'tool_result',
                                    'tool_use_id': block.id,
                                    'content': [{'type': 'text','text': str(info)}] # info
                                })

                        messages.append({
                                'role': 'user',
                                'content': content
                            })
                    
                    else: 
                        block = tool_use_blocks[0]
                        tool_name = block.name
                        tool_input = block.input
                        print(f"\nTool Used: {tool_name}")
                        print(f"Tool Input: {tool_input}")

                        tool = helper.excecute_tool(tool_name)
                        if (tool):
                            info = tool.run(tool_input)
                        else:
                            info = "no data available"
                        messages.append({
                                'role': 'user',
                                'content': [
                                    {
                                        'type': 'tool_result',
                                        'tool_use_id': block.id,
                                        'content': [{'type': 'text','text': str(info)}] # info
                                    }
                                ]
                            })
                    response = client.beta.tools.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        system=system,
                        messages=messages,
                        stream=False,
                        tools=self.tools)
            else:
                messages.append({"role": response.role, "content": response.content})

            betaMessage = ToolsBetaMessage(
                id=response.id,
                content=response.content,
                model=response.model,
                role=response.role,
                stop_reason=response.stop_reason,
                stop_sequence=response.stop_sequence,
                type= response.type,
                usage=response.usage)
            
            helper.add_running_tool_result(tool_execution_id, betaMessage)
        
        except anthropic.AnthropicError as e:
            print('ERROR', e)
            error_code = e.status_code
            error_json = json.loads(e.response.text)
            error_message = error_json["error"]["message"]
            raise CustomError(error_code, error_message)
        except Exception as e:
            context.push()
            app.logger.error(f"Ucnexpected Error: {str(e)}")
            raise CustomError(500, "An unexpected error occurred.")
            
@api.route('/completions/tools/<tool_execution_id>')
class CheckToolExecution(Resource):            

    @api.doc(params={"tool_execution_id": msg.API_DOC_PARAMS_COLLECTION_NAME})        
    def get(self, tool_execution_id):
        if (tool_execution_id):
            tool = helper.get_running_tool(tool_execution_id)
            if(not tool):
                response = {
                    "status": 'DONE',
                    "error": 'INVALID_TOOL_EXECUTION'
                }
            else:
                result = tool.get_result()
                if (not result):
                    response = {
                        "status": 'PROCESSING',
                        "error": None
                    }
                else:
                    helper.delete_running_tool(tool_execution_id)
                    response = {
                        "status": 'DONE',
                        "data": result.to_dict()
                    }
        else:
            response = {
                "status": "DONE",
                "error": "INVALID_TOOL_ID"
            }
        return make_response(jsonify(response), 200)

    
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

        try:
            args = parser.parse_args()
            pdf_file = args.get('pdf', None)
            url = args.get('url', None)
            model = args['model'] if args.get('model') is not None else 'claude-3-opus-20240229'
            system = args['system'] if args.get('system') is not None else 'Summarize this text'
            max_tokens = args['maxTokens'] if args.get('maxTokens') is not None else '1000'
            if pdf_file:
                result = get_pdf_text(pdf_file)
                if (result.get('text')):
                    messages = create_message(result.get('text'))
                    response = client.messages.create(
                        messages=messages, model=model, system=system, max_tokens=int(max_tokens))
                    responseJson = extract_response_data(response)
                    os.remove(result.get('path'))
                    return responseJson, 200
            elif (url and url.lower().endswith('.pdf')):
                pdf_handler = PdfHandler()
                data = pdf_handler.get_pdf_from_url(url)
                pdf_text = extract_text(data)
                if (pdf_text):
                    messages = create_message(pdf_text)
                    response = client.messages.create(
                        messages=messages, model=model, system=system, max_tokens=max_tokens)
                    responseJson = extract_response_data(response)
                    return responseJson, 200
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

@api.route('/cv/analyze')
class AnthropicCVAnalyze(Resource):

    def extract_value(self, text, start_key, end_key):
        start_index = text.find(start_key) + len(start_key)
        end_index = text.find(end_key, start_index)
        if end_index == -1:
            end_index = len(text)
        return text[start_index:end_index].strip()
    
    @api.doc(params={"pdf": msg.API_DOC_PARAMS_PDF_ISOLATE,
                    "jobDescription": msg.API_DOC_PARAMS_JOB_DESCRIPTION,
                    "model": msg.API_DOC_PARAMS_MODEL,
                    "maxTokens": msg.API_DOC_PARAMS_MAX_TOKENS})
    def post(self):
        """
        Analyze a given CV with a given Job Description.

        """
        app.logger.info('handling CV analysis request')
        try:
            args = parser.parse_args()
            pdf_file = args.get('pdf', None)
            job_description = args.get('jobDescription')
            model = args['model'] if args.get('model') is not None else 'claude-3-opus-20240229'
            max_tokens = args['maxTokens'] if args.get('maxTokens') is not None else '1024'
            if pdf_file and job_description:
                resume = get_pdf_text(pdf_file)

                prompt = f"""
                Please analyze the following resume in relation to the given job description:

                Job Description:
                {job_description}

                Resume:
                {resume}

                Provide the following:
                1. A score out of 100 for the matching of the candidate to the job description.
                2. A short paragraph explaining the reasoning behind the score.
                3. Three single-sentence suggestions for improving the resume, separated by newlines and numbered.

                Please format your response as follows:

                Score: {{score}}

                Reasoning: {{reasoning}}

                Suggested Improvements:
                1. {{improvement1}}
                2. {{improvement2}}
                3. {{improvement3}}
                """

                response = client.messages.create(
                    model=model,
                    max_tokens=int(max_tokens),
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                result = str(response.content)

                # Extract the relevant parts from the response
                score = self.extract_value(result, "Score: ", "\\n")
                reasoning = self.extract_value(result, "Reasoning: ", "\\n\\nSuggested Improvements:").replace("\\n", "\n\n").strip()
                improvements_text = self.extract_value(result, "Suggested Improvements:", "\", type='text')]").strip()
                improvements = [imp.strip().replace("\\n", "").split(". ", 1)[-1] for imp in improvements_text.split('\\n') if imp.strip()]

                # Format the output
                output = f"""
                Score: {score}

                Reasoning:\n\n{reasoning}

                Suggested Improvements:
                """

                for i in range(len(improvements)):
                    output += f"\n{i + 1}. {improvements[i]}"

                return output.strip()
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

