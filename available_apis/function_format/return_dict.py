from available_apis.function_format.perplexity_function import PERPLEXITY_CHAT_COMPLETION_FUNCTION_DOCS, perplexity_api_response
from available_apis.function_format.viz_function import visualization_agent, VISUALIZATION_AGENT_FUNCTION_DOCS
import inspect

def get_required_arguments(func):
    signature = inspect.signature(func)
    required_args = [
        param.name for param in signature.parameters.values()
        if param.default == inspect.Parameter.empty and
           param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    return required_args

FUNCTION_APIS_DOCUMENTATION_DICT = {
    "Perplexity": PERPLEXITY_CHAT_COMPLETION_FUNCTION_DOCS,
    "VizAgent": VISUALIZATION_AGENT_FUNCTION_DOCS
    }
FUNCTION_APIS_FUNCTION_DICT = {
    "Perplexity": perplexity_api_response,
    "VizAgent": visualization_agent
    }

# FUNCTION_APIS_REQD_PARAMS_DICT = {
#     "Perplexity": get_required_arguments(perplexity_api_response)
# }

FUNCTION_APIS_REQD_PARAMS_DICT = {
    "Perplexity": {"query": {"type": "string"}},
    "VizAgent": {"query": {"type": "string"}, "response": {"type": "string"}, "index": {"type": "string"}},
}

FUNCTION_APIS_PARAMS_DICT = {
    "Perplexity": {"query": {"type": "string"}, "preplexity_ai_key": {"type": "string"}},
    "VizAgent": {"query": {"type": "string"}, "response": {"type": "string"}, "index": {"type": "string"}},
}