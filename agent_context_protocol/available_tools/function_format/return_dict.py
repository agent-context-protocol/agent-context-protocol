from .perplexity_function import PERPLEXITY_CHAT_COMPLETION_FUNCTION_DOCS, perplexity_api_response
import inspect

def get_required_arguments(func):
    signature = inspect.signature(func)
    required_args = [
        param.name for param in signature.parameters.values()
        if param.default == inspect.Parameter.empty and
           param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    return required_args

FUNCTION_TOOLS_DOCUMENTATION_DICT = {
    "Perplexity": PERPLEXITY_CHAT_COMPLETION_FUNCTION_DOCS
    }
FUNCTION_TOOLS_FUNCTION_DICT = {
    "Perplexity": perplexity_api_response
    }

# FUNCTION_TOOLS_REQD_PARAMS_DICT = {
#     "Perplexity": get_required_arguments(perplexity_api_response)
# }

FUNCTION_TOOLS_REQD_PARAMS_DICT = {
    "Perplexity": {"query": {"type": "string"}},
}

FUNCTION_TOOLS_PARAMS_DICT = {
    "Perplexity": {"query": {"type": "string"}, "preplexity_ai_key": {"type": "string"}}
}