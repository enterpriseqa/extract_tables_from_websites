
import asyncio
import os
from agent.extract_table_multi_model_agent import MultiModalTableInterpreter, process_folder_sequentially
from lib.extract_table_as_image import extract_table_data_as_images
from utils.utils import compare_json_files_deepdiff, generate_random_prefix


#TARGET_URL = "https://datatables.net/examples/api/multi_filter.html"
#IMAGES_OUTPUT_DIR = "logs/datatables/api_multi_filter"

TARGET_URL = "https://designsystem.digital.gov/components/table/"
IMAGES_OUTPUT_DIR = "logs/digital_gov/components_table"




if __name__ == "__main__":
    extract_table_data_as_images(TARGET_URL, IMAGES_OUTPUT_DIR)
    agent_sonet_35_bedrock = MultiModalTableInterpreter(
    provider="bedrock",
    model_name="us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    log_base_path="./logs/bedrock_sonet35"
    )

    agent_sonet_37_bedrock = MultiModalTableInterpreter(
    provider="bedrock",
    model_name="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    log_base_path="./logs/bedrock_sonet37"
    )
    agents = [agent_sonet_35_bedrock, agent_sonet_37_bedrock]

    output_paths = []
    for agent in agents:
        random_prefix = generate_random_prefix(5)
        log_path = f"logs/{random_prefix}"
        os.makedirs(log_path, exist_ok=True)
        output_path = f"{log_path}/extracted_data.json"
        output_paths.append(output_path)
        asyncio.run(process_folder_sequentially(
            request_id_prefix=1,
            folder_path=IMAGES_OUTPUT_DIR,
            agent=agent,
            output_path=output_path
        ))
    compare_json_files_deepdiff(output_paths)    