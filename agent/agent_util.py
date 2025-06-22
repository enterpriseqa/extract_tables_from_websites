import datetime
import json
import os
from utils.qa_logging import log_message
from langchain_core.messages import HumanMessage, SystemMessage
import logging

def generate_system_prompt_with_json_data_for_multiple_images(model_prompt_file_path: str, json_content: str,
                                                              screenshots, interactive_elements: str = None):
    system_prompt = generate_prompt_messages(
        model_prompt_file_path)
    if (system_prompt == None):
        log_message("system_prompt is None", logging.ERROR)
        raise Exception("Not able to generate system prompt")
    system_information = f"Today's date - {datetime.datetime.today().strftime('%Y-%m-%d')}\n"
    system_message = SystemMessage(
        content=system_information + system_prompt
    )

    contents = f'{json.dumps(json_content)}'
    if (interactive_elements is not None):
        contents += f"\n\n{interactive_elements}"
    contents = contents.replace("...", "")
    human_message_without_image = HumanMessage(
        content=[
            {
                'type': 'text', 'text': contents
            }
        ])

    content_array = [
        {  # <--- No extra list here
            'type': 'image_url',
            'image_url': {'url': f'data:image/jpeg;base64,{screenshot}'},
        }
        for screenshot in screenshots
    ]
    
    content_array.append( {
                    'type': 'text', 'text': contents
                })
    human_message = None
    if (screenshots):
        human_message = HumanMessage(
            content_array)
    else:
        human_message = HumanMessage(
            content=[
                {
                    'type': 'text', 'text': contents
                }
            ])

    return (system_message, human_message, human_message_without_image)


def generate_system_prompt_with_json_data(model_prompt_file_path: str, json_content: str, screenshot, interactive_elements: str = None):
    system_prompt = generate_prompt_messages(
        model_prompt_file_path)
    if (system_prompt == None):
        log_message("system_prompt is None", logging.ERROR)
        raise Exception("Not able to generate system prompt")
    system_information = f"Today's date - {datetime.datetime.today().strftime('%Y-%m-%d')}\n"
    system_message = SystemMessage(
        content=system_information + system_prompt
    )

    contents = f'{json.dumps(json_content)}'
    if (interactive_elements is not None):
        contents += f"\n\n{interactive_elements}"
    contents = contents.replace("...", "")
    human_message_without_image = HumanMessage(
        content=[
            {
                'type': 'text', 'text': contents
            }
        ])

    human_message = None
    if (screenshot):
        human_message = HumanMessage(
            content=[
                {
                    'type': 'image_url',
                            'image_url': {'url': f'data:image/jpeg;base64,{screenshot}'},
                },
                {
                    'type': 'text', 'text': contents
                }
            ])
    else:
        human_message = HumanMessage(
            content=[
                {
                    'type': 'text', 'text': contents
                }
            ])

    return (system_message, human_message, human_message_without_image)

def combine_system_prompt_input_files(txt_file_path, json_file_path):
    try:
        # Read the .txt file
        with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
            txt_content = txt_file.read()
    except FileNotFoundError:
        log_message(
            f"Error: .txt file not found at {txt_file_path}", logging.ERROR)
        return None
    except Exception as e:
        log_message(f"Error reading .txt file: {e}", logging.ERROR)
        return None

    if (json_file_path is None):
        return txt_content

    try:
        # Read the .json file
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
            # Convert JSON to a string with indentation for readability
            json_content = json.dumps(json_data, indent=4)
    except FileNotFoundError:
        log_message(
            f"Error: .json file not found at {json_file_path}", logging.ERROR)
        return None
    except json.JSONDecodeError:
        log_message(
            f"Error: Invalid JSON format in {json_file_path}", logging.ERROR)
        return None
    except Exception as e:
        log_message(f"Error reading .json file: {e}", logging.ERROR)
        return None

    # Concatenate the contents
    combined_string = txt_content + "\n\n" + \
        json_content  # Add a separator for clarity

    return combined_string


def generate_prompt_messages(model_file_path):
    current_directory = os.getcwd()

    txt_file_full_path = os.path.join(current_directory, model_file_path)
    #json_file_full_path = os.path.join(current_directory, input_file_path)
    combined_string = combine_system_prompt_input_files(
        txt_file_full_path, None)

    if combined_string:
        # Print to the console
        log_message(f"Prompt message: {combined_string}")
        with open("combined_file.txt", "w", encoding="utf-8") as outfile:
            outfile.write(combined_string)
    return combined_string

def generate_input_messages(model_prompt_file_path: str, input_file_path: str, task_description: str, step_details, interactive_elements, screenshot):
    log_message("model prompt file path:{model_prompt_file_path}")
    log_message("input file path:{input_file_path}")
    
    system_prompt = generate_prompt_messages(
        model_prompt_file_path, input_file_path)
    if (system_prompt == None):
        log_message("system_prompt is None", logging.ERROR)
        raise Exception("Not able to generate system prompt")
    system_information = f"Today's date - {datetime.datetime.today().strftime('%Y-%m-%d')}\n"
    system_message = SystemMessage(
        content=system_information + system_prompt
    )
    contents = f'Task:{task_description}\n\n Step Input: \n{json.dumps(step_details)}\n\n Interactive Elements: \n {interactive_elements}'
    contents = contents.replace("...", "")
    human_message_without_image = HumanMessage(
        content=[
            {
                'type': 'text', 'text': contents
            }
        ])

    human_message = None
    if (screenshot):
        human_message = HumanMessage(
            content=[
                {
                    'type': 'text', 'text': contents
                },
                {
                    'type': 'image_url',
                            'image_url': {'url': f'data:image/png;base64,{screenshot}'},
                }
            ])
    else:
        human_message = HumanMessage(
            content=[
                {
                    'type': 'text', 'text': contents
                }
            ])

    return (system_message, human_message, human_message_without_image)