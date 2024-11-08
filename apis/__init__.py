from flask_restx import Api
from .vertex_resource import api as vertex_namespace, VertexGeminiCompletionRes
from .llms_resource import api as llms_namespace
from .xai_resource import api as xai_namespace
from .collections import api as collections_namespace
from .openai_resource import api as openai_namespace
from .anthropic import api as anthropic_namespace, AnthropicCompletionRes
from .luma import api as lumaai_namespace


api = Api(
    title='LLMs Api Hub',
    version='1.0',
    description='Large Language Models (LLM) API Hub',
)

api.add_namespace(vertex_namespace)
api.add_namespace(llms_namespace)
api.add_namespace(collections_namespace)
api.add_namespace(openai_namespace)
api.add_namespace(anthropic_namespace)
api.add_namespace(lumaai_namespace)
api.add_namespace(xai_namespace)