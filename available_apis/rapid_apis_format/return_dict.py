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

# Example usage
json_file = './available_apis/rapid_apis_format/executable-spec-converted.json'
RAPID_APIS_DICT = create_rapid_apis_dict(json_file)