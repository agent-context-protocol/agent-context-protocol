import yaml

def convert_yml_to_string_fully(yml_file):
    # Open and load the YAML file
    with open(yml_file, 'r') as file:
        yml_data = yaml.safe_load(file)

    # Create and return a formatted string
    return dict_to_string(yml_data)

def convert_yml_to_string(yml_file, api_path):
    # Open and load the YAML file
    with open(yml_file, 'r') as file:
        yml_data = yaml.safe_load(file)

    # Parse general info from YAML
    result = ""
    result += dict_to_string(yml_data, ["openapi", "servers", "info", "tags"])  # Common parts
    result += "\n"

    # Check if the API path exists in the YAML
    if api_path in yml_data["paths"]:
        # Extract path-specific data
        result += f"paths:\n"
        result += dict_to_string({api_path: yml_data["paths"][api_path]})
    else:
        result += f"Path {api_path} not found in the YAML file.\n"
    
    # Append components section (common for all paths)
    result += "\ncomponents:\n"
    result += dict_to_string(yml_data["components"])

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

# Example Usage
# print(convert_yml_to_string("/available_tools/openapi_format/stackexchange.yaml", "/questions"))
# print(convert_yml_to_string_fully("weather_api.yml"))

OPENAPI_TOOLS_DICT = {
    "Open-Meteo": convert_yml_to_string_fully("./available_tools/openapi_format/weather_api.yml"),
    "Stack_Exchange_Questions": convert_yml_to_string("./available_tools/openapi_format/stackexchange.yaml", "/questions"),
    "Stack_Exchange_Answers": convert_yml_to_string("./available_tools/openapi_format/stackexchange.yaml", "/answers"),
    "Stack_Exchange_Users": convert_yml_to_string("./available_tools/openapi_format/stackexchange.yaml", "/users")
}