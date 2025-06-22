
import asyncio
import os
from agent.extract_table_multi_model_agent import MultiModalTableInterpreter, process_folder_sequentially, process_images_in_folder
from utils.utils import compare_json_files_deepdiff, generate_random_prefix

model_ids = ["us.anthropic.claude-3-5-sonnet-20240620-v1:0", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"]

if __name__ == "__main__":
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

    images_path = "logs/datatables/ajax"
    output_paths = []
    for agent in agents:
        random_prefix = generate_random_prefix(5)
        log_path = f"logs/{random_prefix}"
        os.makedirs(log_path, exist_ok=True)
        output_path = f"{log_path}/extracted_data.json"
        output_paths.append(output_path)
        asyncio.run(process_folder_sequentially(
            request_id_prefix=1,
            folder_path="logs/datatables/ajax",
            agent=agent,
            output_path=output_path
        ))
    compare_json_files_deepdiff(output_paths)
