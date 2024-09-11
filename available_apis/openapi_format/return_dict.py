import yaml

def convert_yml_to_text(yml_file, output_txt_file):
    # Open and load the YAML file
    with open(yml_file, 'r') as file:
        yml_data = yaml.safe_load(file)

    # Create and write to the text file
    with open(output_txt_file, 'w') as file:
        for key, value in yml_data.items():
            file.write(f"{key}:\n")
            if isinstance(value, dict):
                write_dict_to_file(value, file, indent=2)
            else:
                file.write(f"  {value}\n")

def write_dict_to_file(data_dict, file, indent=0):
    # Recursive function to handle nested dictionaries and lists
    for key, value in data_dict.items():
        file.write(f"{' ' * indent}{key}:\n")
        if isinstance(value, dict):
            write_dict_to_file(value, file, indent + 2)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    write_dict_to_file(item, file, indent + 2)
                else:
                    file.write(f"{' ' * (indent + 2)}- {item}\n")
        else:
            file.write(f"{' ' * (indent + 2)}{value}\n")

# Usage
yml_file = "weather_api.yml"  # Your YAML file path
output_txt_file = "formatted_open_meteo.txt"  # Output text file path

convert_yml_to_text(yml_file, output_txt_file)
