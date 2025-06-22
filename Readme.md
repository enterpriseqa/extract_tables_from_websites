# 🧾 Extract Tables from Websites

A two-step process to extract **HTML tables from websites**:

1. **Render and capture tables as images**
2. **Use OCR to convert images to structured JSON**

This approach improves reliability by capturing the **actual visual layout** of a webpage before using OCR to extract structured data, helping with tricky cases like dynamic content, styled tables, or merged cells.

---

## 📦 Features

- Extract tables using a headless browser
- Detect and crop only table elements
- OCR-based table structure recognition
- Output as clean JSON with headers and rows

---

## 🔧 Installation

```bash
git clone https://github.com/enterpriseqa/extract_tables_from_websites.git
cd extract_tables_from_websites
pip install -r requirements.txt
```

## Example Usage

```
TARGET_URL = "https://designsystem.digital.gov/components/table/"
IMAGES_OUTPUT_DIR = "logs/digital_gov/components_table"


if __name__ == "__main__":
    # First Download the tables as images from the webpage

    extract_table_data_as_images(TARGET_URL, IMAGES_OUTPUT_DIR)

    # Using two models to evaluate

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

    # Extract the table as json from the images.

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

    Note: Works for most of the standard tables. This utility is being used by QAAgent to extract the tables and compare them with expected results.
    
```

## Dependencies

    Playwright (for rendering and scraping)

    OpenCV / PIL (for image processing)

    Python ≥ 3.11



## ✅ Benefits of This Approach

    Works with complex/dynamic tables

    Captures visually styled content

    Avoids messy HTML parsing

    Output is structured, clean JSON

## 📬 Contributing

Feel free to open issues or pull requests to improve table detection, OCR accuracy, or add support for new languages.


## 📄 License

MIT License