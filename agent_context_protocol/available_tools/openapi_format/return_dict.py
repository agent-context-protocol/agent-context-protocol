import yaml
from importlib import resources
from agent_context_protocol import external_env_details  # adjust if your module path differs

def convert_yml_to_string_fully(file_name):
    with resources.open_text(external_env_details, file_name) as file:
        yml_data = yaml.safe_load(file)
    return dict_to_string(yml_data)

def convert_yml_to_string(file_name, api_path):
    with resources.open_text(external_env_details, file_name) as file:
        yml_data = yaml.safe_load(file)

    result = ""
    result += dict_to_string(yml_data, ["openapi", "servers", "info", "tags"])
    result += "\n"

    if api_path in yml_data.get("paths", {}):
        result += "paths:\n"
        result += dict_to_string({api_path: yml_data["paths"][api_path]})
    else:
        result += f"Path {api_path} not found in the YAML file.\n"

    result += "\ncomponents:\n"
    result += dict_to_string(yml_data.get("components", {}))

    return result

def dict_to_string(data_dict, keys_to_include=None, indent=0):
    result = ""
    if isinstance(data_dict, dict):
        for key, value in data_dict.items():
            if keys_to_include is None or key in keys_to_include:
                result += f"{' ' * indent}{key}:\n"
                if isinstance(value, dict):
                    result += dict_to_string(value, None, indent + 2)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            result += dict_to_string(item, None, indent + 2)
                        else:
                            result += f"{' ' * (indent + 2)}- {item}\n"
                else:
                    result += f"{' ' * (indent + 2)}{value}\n"
    return result

# Construct dictionary from packaged YAMLs
OPENAPI_TOOLS_DICT = {
    "Open-Meteo": convert_yml_to_string_fully("weather_api.yml"),
    "Stack_Exchange_Questions": convert_yml_to_string("stackexchange.yaml", "/questions"),
    "Stack_Exchange_Answers": convert_yml_to_string("stackexchange.yaml", "/answers"),
    "Stack_Exchange_Users": convert_yml_to_string("stackexchange.yaml", "/users"),
}
