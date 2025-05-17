import json
from importlib import resources
from acpkit import external_env_details

def get_api_details(api_name, data):
    if api_name in data:
        api_details = data[api_name]
        result_string = f"API Name: {api_name}\n"
        for key, value in api_details.items():
            if isinstance(value, dict):
                result_string += f"{key}:\n"
                for sub_key, sub_value in value.items():
                    result_string += f"  {sub_key}: {sub_value}\n"
            else:
                result_string += f"{key}: {value}\n"
        return result_string
    else:
        raise ValueError(f"API with name '{api_name}' not found.")

def create_rapid_apis_dict(file_name):
    with resources.open_text(external_env_details, file_name) as file:
        data = json.load(file)
    return {api_name: get_api_details(api_name, data) for api_name in data}

def create_required_params_dict(file_name, required_params_bool=False):
    with resources.open_text(external_env_details, file_name) as file:
        apis_data = json.load(file)

    required_query_parameters = {}
    for api_name, api_details in apis_data.items():
        required_params = {}
        query_path_name = (
            "path_parameters" if "path_parameters" in api_details else 
            "query_parameters" if "query_parameters" in api_details else 
            None
        )
        if not query_path_name:
            raise ValueError("The only options are path_parameters and query_parameters.")

        for param, param_details in api_details[query_path_name].items():
            if not required_params_bool or param_details.get("required"):
                required_params[param] = {
                    "type": param_details["type"],
                    "description": param_details["description"]
                }

        required_query_parameters[api_name] = required_params

    return required_query_parameters

# Example usage
json_file = "executable-spec-converted.json"
RAPIDAPI_TOOLS_DICT = create_rapid_apis_dict(json_file)
RAPIDAPI_REQD_PARAMS_DICT = create_required_params_dict(json_file, True)
RAPIDAPI_PARAMS_DICT = create_required_params_dict(json_file)
