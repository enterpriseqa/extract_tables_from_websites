# --- CONFIGURATION ---
from lib.extract_table_as_image import extract_table_data_as_images


#TARGET_URL = "https://ninjatables.com/examples-of-data-table-design-on-website/?srsltid=AfmBOordnFfvQQ2RpFYi4GJj2c0m7OUHu1SZxemxuuiG7IfSiJc3uhBD"
#OUTPUT_DIR = "logs/ninjatables"

#TARGET_URL = "https://datatables.net/examples/basic_init/zero_configuration.html"
#OUTPUT_DIR = "logs/datatables/zero_config"

TARGET_URL = "https://datatables.net/examples/data_sources/ajax.html"
OUTPUT_DIR = "logs/datatables/ajax"



if __name__ == "__main__":
    extract_table_data_as_images(TARGET_URL, OUTPUT_DIR)