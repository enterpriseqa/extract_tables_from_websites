from abc import abstractmethod
import asyncio
import base64
from dataclasses import dataclass
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict
from langchain_aws import ChatBedrock
import natsort


from agent.agent_util import generate_system_prompt_with_json_data_for_multiple_images
from utils.qa_logging import log_message, set_thread_context_id
from langchain_core.messages import AIMessage
from utils.utils import generate_random_prefix
from utils.utils import compare_json_files_deepdiff

model_ids = ["us.anthropic.claude-3-5-sonnet-20240620-v1:0", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"]


TABLE_EXTRACTOR_MODEL_FILE_PATH =  "model/model_table_extractor.txt"

def get_image_as_base64(image_path):
    """
    Reads an image file, encodes it to Base64, and returns the string.
    Returns None if an error occurs.
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found at '{image_path}'")
        return None

    try:
        with open(image_path, "rb") as image_file:
            binary_data = image_file.read()
            base64_encoded_bytes = base64.b64encode(binary_data)
            base64_encoded_string = base64_encoded_bytes.decode('utf-8')
            return base64_encoded_string
    except Exception as e:
        print(f"Error encoding file {image_path}: {e}")
        return None


class TableInterpreterAgent():
    def __init__(
            self,
            model_id: str,
            log_base_path: str):
        self.log_base_path = log_base_path
        self.system_prompt_path = TABLE_EXTRACTOR_MODEL_FILE_PATH
        self.model_id = model_id


    def get_llm(self):
        return ChatBedrock(
            model_id=self.model_id,
            temperature=0.0,
            max_tokens=5000)

    async def call_llm_agent_with_retry(self, llm_with_schema, messages, retries=15):
        for i in range(retries):
            try:
                response: AIMessage = await llm_with_schema.ainvoke(messages)
                return response
            except Exception as e:
                print(e)
        raise Exception("API call failed after retries")

    async def call_agent(self, request_id: int, json_data, screenshots) -> Any | None:
        random_prefix = generate_random_prefix(5)
        context_id = f"{random_prefix}-{threading.get_native_id()}"
        set_thread_context_id(context_id)
        
        log_message("generating system input message for llm")

        (system_message, human_message, human_message_without_image) = generate_system_prompt_with_json_data_for_multiple_images(
            self.system_prompt_path, json_data,screenshots)

        ai_step_input_path = f'{self.log_base_path}/ai_input_table_extract{request_id}.txt'

        log_message("writing system input message for llm")
        with open(ai_step_input_path, 'w', encoding='utf-8') as f:
            f.write(f'{[system_message, human_message_without_image]}')

        messages = [system_message, human_message]

        log_message("calling llm")

        llm = self.get_llm()

        # type: ignore
        response: AIMessage = await self.call_llm_agent_with_retry(llm, messages)
        parsed_json = json.loads(response.content)

        log_message(f"response from llm: {parsed_json}")
        ai_step_output_path = f'{self.log_base_path}/ai_output_table_extract{request_id}.txt'

        with open(ai_step_output_path, 'w', encoding='utf-8') as f:
            f.write(f'{parsed_json}')
        return parsed_json



def process_images_in_folder(request_id, folder_path, agent, output_path):
    """
    Loops through a folder, converts each image to Base64, and calls the agent.
    """
    # 1. Check if the folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return

    # 2. Define supported image extensions
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

    # 3. Loop through all files in the directory
    print(f"Starting to process images in folder: {folder_path}\n")
    extracted_data = []
    table_images = [] 
    for filename in natsort.natsorted(os.listdir(folder_path)):
        if filename.lower().endswith(supported_extensions):
            image_path = os.path.join(folder_path, filename)
            file_name_without_ext = Path(image_path).stem
            print(f"--- Processing: {image_path} ---")
            table_image_b64 = get_image_as_base64(image_path)
            if table_image_b64:
                table_images.append(table_image_b64)
    try:
        print(f"Successfully loaded and encoded files. Calling agent...")
        response = asyncio.run(agent.call_agent(request_id, "{}", table_images))
        extracted_data.append(response)
        print(f"Agent response for {filename}: {response}") # Or handle the response as needed
    except Exception as e:
        print(f"An error occurred while calling the agent for {filename}: {e}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(extracted_data))

    print("Finished processing all images in the folder.")
    return extracted_data


if __name__ == "__main__":
    #images_path = "logs/table_extract/AhVuh/input_images"
    images_path = "logs/datatables/ajax"
    output_paths = []
    for model_id in model_ids:
        random_prefix = generate_random_prefix(5)
        log_path = f"logs/{random_prefix}"
        output_path = f"{log_path}/table_data.json" 
        os.makedirs(log_path, exist_ok=True)
        output_paths.append(output_path)
        table_extractor_agent = TableInterpreterAgent(model_id, log_path)
        process_images_in_folder(random_prefix, images_path, table_extractor_agent, output_path)
    
    compare_json_files_deepdiff(output_paths)
        
    