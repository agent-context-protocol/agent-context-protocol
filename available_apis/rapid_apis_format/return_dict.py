import json

def get_api_details(api_name, data):
    """
    Returns the formatted string for the given API name from the dictionary of APIs.
    """
    if api_name in data:
        api_details = data[api_name]
        
        # Convert the API details dictionary into a formatted string
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

def create_rapid_apis_dict(json_file):
    """
    Creates a dictionary with the API names as keys and their details in string format as values.
    """
    # Load the dictionary of dictionaries from the JSON file
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Create the dictionary where the key is the API name and value is the formatted string
    rapid_apis_dict = {api_name: get_api_details(api_name, data) for api_name in data}

    return rapid_apis_dict

def create_required_params_dict(json_file, required_params_bool = False):
    # Load the dictionary of dictionaries from the JSON file
    with open(json_file, 'r') as file:
        apis_data = json.load(file)

    # print("apis_data : ",apis_data)

    # Initialize the dictionary
    required_query_parameters = {}

    # Iterate through each API
    for api_name, api_details in apis_data.items():
        required_params = {}
        # print("api_name : ",api_name)
        query_path_name = ""
        if "path_parameters" in api_details:
            query_path_name = "path_parameters"
        elif "query_parameters" in api_details:
            query_path_name = "query_parameters"
        else:
            raise ValueError("The only options are path_parameters and query_parameters.")
        for param, param_details in api_details[query_path_name].items():
            if not required_params_bool or param_details.get("required"):
            # if param_details["required"]:
                required_params[param] = {
                    "type": param_details["type"],
                    "description": param_details["description"]
            }
        required_query_parameters[api_name] = required_params

    # Now 'required_query_parameters' contains only the required parameters for each API
    # print(json.dumps(required_query_parameters, indent=4))

    return required_query_parameters

# Example usage
json_file = './available_apis/rapid_apis_format/executable-spec-converted.json'
# json_file = 'executable-spec-converted.json'
RAPID_APIS_DICT = create_rapid_apis_dict(json_file)
RAPID_REQD_PARAMS_DICT = create_required_params_dict(json_file, True)
RAPID_PARAMS_DICT = create_required_params_dict(json_file)
# print("RAPID_PARAMS_DICT:",RAPID_PARAMS_DICT)