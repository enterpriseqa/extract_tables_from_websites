import os
import json
import asyncio
import base64
import threading
import uuid
from pathlib import Path
from typing import Any, List, Tuple

import natsort
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# --- Import the necessary LangChain chat models ---
from langchain_aws import ChatBedrock
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from agent.agent_util import generate_system_prompt_with_json_data_for_multiple_images
from utils.qa_logging import log_message, set_thread_context_id
from utils.utils import generate_random_prefix

# --- Mock/Helper functions (assuming their original implementation) ---
# These are kept from your original code or are placeholders.

def get_image_as_base64(image_path: str) -> str | None:
    """Reads an image and returns it as a Base64 encoded string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

# Assume this file contains your system prompt template
TABLE_EXTRACTOR_MODEL_FILE_PATH = "model/model_table_extractor.txt"


# --- Refactored Agent Class ---

class MultiModalTableInterpreter:
    """
    An agent that uses a multimodal LLM to interpret tables from images.
    This class is provider-agnostic and supports OpenAI, Google, and AWS Bedrock.
    """
    def __init__(
        self,
        provider: str,
        model_name: str,
        log_base_path: str,
        system_prompt_path: str = TABLE_EXTRACTOR_MODEL_FILE_PATH
    ):
        """
        Initializes the agent.

        Args:
            provider (str): The LLM provider to use ('openai', 'google', 'bedrock').
            model_name (str): The specific model name for the provider
                              (e.g., 'gpt-4o', 'gemini-1.5-pro-latest', 'anthropic.claude-3-sonnet-v1:0').
            log_base_path (str): The base path for saving logs.
            system_prompt_path (str): Path to the file containing the system prompt.
        """
        if provider not in ["openai", "google", "bedrock"]:
            raise ValueError("Provider must be one of 'openai', 'google', or 'bedrock'")

        self.provider = provider
        self.model_name = model_name
        self.log_base_path = log_base_path
        self.system_prompt_path = system_prompt_path
        
        # Ensure log directory exists
        os.makedirs(self.log_base_path, exist_ok=True)

    def _get_llm(self):
        """
        Factory method to get the appropriate LangChain chat model instance.
        """
        common_params = {
            "model": self.model_name,
            "temperature": 0.0,
            "max_tokens": 4096  # Standardized token limit, adjust if needed
        }
        
        log_message(f"Initializing LLM for provider: '{self.provider}' with model: '{self.model_name}'")

        if self.provider == "openai":
            return ChatOpenAI(**common_params)
        elif self.provider == "google":
            # ChatGoogleGenerativeAI uses 'model_name' instead of 'model'
            common_params["model_name"] = common_params.pop("model")
            return ChatGoogleGenerativeAI(**common_params)
        elif self.provider == "bedrock":
            # ChatBedrock uses 'model_id'
            common_params["model_id"] = common_params.pop("model")
            return ChatBedrock(**common_params)
        else:
            # This case is already handled in __init__, but good for safety
            raise NotImplementedError(f"Provider '{self.provider}' is not supported.")

    def _generate_prompt_messages(
        self,
        json_data: str,
        screenshots: List[str]
    ) -> Tuple[SystemMessage, HumanMessage, str]:
        """
        Generates the system and human messages in the standard LangChain multimodal format.
        """
        with open(self.system_prompt_path, 'r', encoding='utf-8') as f:
            system_prompt_template = f.read()

        # For this example, we'll just pass the json_data as the user's text prompt
        user_text_prompt = f"Here is the context for the tables: {json_data}. Please analyze the following images."

        system_message = SystemMessage(content=system_prompt_template)

        # LangChain's standard for multimodal input is a list of content blocks
        human_message_content = [{"type": "text", "text": user_text_prompt}]
        for b64_image in screenshots:
            human_message_content.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{b64_image}"
            })

        human_message = HumanMessage(content=human_message_content)
        
        # Also return a version without images for logging purposes
        human_message_without_image = HumanMessage(content=user_text_prompt)

        return system_message, human_message, str(human_message_without_image)


    async def _call_llm_with_retry(self, llm, messages, retries=5):
        """
        Calls the LLM with a simple retry mechanism.
        Note: LangChain has a built-in `with_retry` method which is more robust.
        """
        for i in range(retries):
            try:
                response: AIMessage = await llm.ainvoke(messages)
                return response
            except Exception as e:
                log_message(f"API call attempt {i+1}/{retries} failed: {e}")
                if i == retries - 1: # Last attempt
                    raise Exception("API call failed after all retries") from e
                await asyncio.sleep(2 ** i) # Exponential backoff

    async def call_agent(self, request_id: int, json_data: str, screenshots: List[str]) -> Any | None:
        """
        Main method to process a request with images and context.
        """
        context_id = f"{generate_random_prefix(5)}-{threading.get_native_id()}"
        set_thread_context_id(context_id)
        
        log_message("Generating system and human messages for LLM")
        (system_message, human_message, human_message_without_image) = generate_system_prompt_with_json_data_for_multiple_images(
            self.system_prompt_path, json_data, screenshots
        )

        # Log the text part of the input for debugging
        ai_step_input_path = f'{self.log_base_path}/ai_input_table_extract_{request_id}.txt'
        log_message(f"Writing text input for LLM to {ai_step_input_path}")
        with open(ai_step_input_path, 'w', encoding='utf-8') as f:
            f.write(f'System: {system_message.content}\n\nHuman: {human_message_without_image}')

        messages = [system_message, human_message]

        log_message("Calling LLM...")
        llm = self._get_llm()

        response: AIMessage = await self._call_llm_with_retry(llm, messages)
        
        # The response content should be a JSON string, as requested in the prompt
        try:
            # Some models might wrap the JSON in markdown ```json ... ```
            cleaned_content = response.content.strip().removeprefix("```json").removesuffix("```").strip()
            parsed_json = json.loads(cleaned_content)
        except (json.JSONDecodeError, AttributeError) as e:
            log_message(f"Failed to parse JSON from LLM response. Error: {e}")
            log_message(f"Raw response content: {response.content}")
            # Return the raw content or handle the error as needed
            return {"error": "Failed to parse JSON response", "content": response.content}


        log_message(f"Successfully parsed response from LLM.")
        ai_step_output_path = f'{self.log_base_path}/ai_output_table_extract_{request_id}.json'
        with open(ai_step_output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2)
            
        return parsed_json

async def process_folder_sequentially(request_id_prefix, folder_path, agent: MultiModalTableInterpreter, output_path):
    """
    Loops through a folder, calls the agent for EACH image, and aggregates results.
    This is the most reliable method for consistent output.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return

    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    print(f"Starting to process images in folder: {folder_path}\n")

    # This list will hold the final, ordered results.
    all_extracted_data = []

    image_files = [f for f in natsort.natsorted(os.listdir(folder_path)) if f.lower().endswith(supported_extensions)]

    for i, filename in enumerate(image_files):
        image_path = os.path.join(folder_path, filename)
        print(f"--- Processing image {i+1}/{len(image_files)}: {filename} ---")

        table_image_b64 = get_image_as_base64(image_path)
        if not table_image_b64:
            # Add a placeholder for failed encoding, or handle as needed
            all_extracted_data.append({"error": "Failed to encode image", "filename": filename})
            continue

        try:
            # The agent is now called with a list containing just ONE image.
            # The request_id can be made unique for better logging.
            image_request_id = f"{request_id_prefix}_{Path(filename).stem}"
            
            # We expect the agent to return the data for this single image.
            # The prompt will guide it to return `[]` for non-tables.
            response = await agent.call_agent(
                request_id=image_request_id,
                json_data="{}", # Context for this specific image
                screenshots=[table_image_b64] # Pass as a list with one item
            )
            
            # The original `call_agent` was designed to return a single JSON object,
            # which might be a list of tables. We need to handle this.
            # If the agent returns [[...]], we take the first element.
            if isinstance(response, list) and len(response) == 1:
                 single_table_data = response[0]
            else:
                 # This case handles if the model just returns the inner array directly
                 single_table_data = response

            all_extracted_data.append(single_table_data)
            print(f"Agent response for {filename}: {'Table found' if single_table_data else 'No table found'}")

        except Exception as e:
            print(f"An error occurred while calling the agent for {filename}: {e}")
            all_extracted_data.append({"error": str(e), "filename": filename})

    print(f"\nFinished processing all images. Writing aggregated results to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_extracted_data, f, indent=2)

    return all_extracted_data


async def process_images_in_folder(request_id, folder_path, agent: MultiModalTableInterpreter, output_path):
    """
    Loops through a folder, converts each image to Base64, and calls the agent.
    (This function is largely unchanged as it interacts with the agent's public API)
    """
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return

    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    print(f"Starting to process images in folder: {folder_path}\n")
    
    table_images = []
    for filename in natsort.natsorted(os.listdir(folder_path)):
        if filename.lower().endswith(supported_extensions):
            image_path = os.path.join(folder_path, filename)
            print(f"--- Loading: {image_path} ---")
            table_image_b64 = get_image_as_base64(image_path)
            if table_image_b64:
                table_images.append(table_image_b64)

    if not table_images:
        print("No supported images found in the folder.")
        return

    try:
        print(f"Successfully loaded and encoded {len(table_images)} files. Calling agent...")
        # The agent now handles multiple images in a single call
        response = await agent.call_agent(request_id, "{}", table_images)
        
        print(f"Agent response received. Writing to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2)
        
        print("Finished processing all images in the folder.")
        return response
    except Exception as e:
        print(f"An error occurred while calling the agent: {e}")