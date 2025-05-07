"""
Available Tools Package

Contains various API tools and utilities organized by format type.
"""

from .function_format.return_dict import (
    FUNCTION_TOOLS_DOCUMENTATION_DICT,
    FUNCTION_TOOLS_REQD_PARAMS_DICT,
    FUNCTION_TOOLS_PARAMS_DICT,
    FUNCTION_TOOLS_FUNCTION_DICT
)

from .hardcoded_format.return_dict import HARDCODED_TOOLS_DICT

from .openapi_format.return_dict import OPENAPI_TOOLS_DICT

from .rapid_apis_format.return_dict import (
    RAPIDAPI_TOOLS_DICT,
    RAPIDAPI_REQD_PARAMS_DICT,
    RAPIDAPI_PARAMS_DICT
)

__all__ = [
    # Function format tools
    "FUNCTION_TOOLS_DOCUMENTATION_DICT",
    "FUNCTION_TOOLS_REQD_PARAMS_DICT",
    "FUNCTION_TOOLS_PARAMS_DICT",
    "FUNCTION_TOOLS_FUNCTION_DICT",
    
    # Hardcoded format tools
    "HARDCODED_TOOLS_DICT",
    
    # OpenAPI format tools
    "OPENAPI_TOOLS_DICT",
    
    # RapidAPI format tools
    "RAPIDAPI_TOOLS_DICT",
    "RAPIDAPI_REQD_PARAMS_DICT",
    "RAPIDAPI_PARAMS_DICT"
]