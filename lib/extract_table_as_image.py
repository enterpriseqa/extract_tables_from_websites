import os
import time
from playwright.sync_api import sync_playwright, Page, Locator

MIN_SECTION_HEIGHT = 50

# A revised, simpler list of selectors.
# For this page, 'div#content > table' is the most precise and effective.
SELECTORS_TO_TRY = [
    "div#content > table",  # The BEST selector: find all tables inside the main content div.
    "table[border='1']",    # A good alternative: find all tables that have a border.
    "table"                 # The most general fallback: find any table on the page.
]

def find_best_section_locator(page: Page) -> Locator | None:
    """Tries a list of selectors on the main page and returns the first that works."""
    print("\n--- Finding the best layout selector on the page ---")
    for selector in SELECTORS_TO_TRY:
        print(f"Trying selector: '{selector}'...")
        try:
            count = page.locator(selector).count()
            if count > 0:
                print(f"✅ Success! Found {count} elements with '{selector}'. Using this selector.")
                return page.locator(selector)
        except Exception as e:
            print(f"Selector '{selector}' failed: {e}")
            continue
    print("❌ Failed to find a suitable layout selector.")
    return None

def filter_and_capture_sections(section_locator: Locator, output_dir: str):
    """Filters locators by size and captures screenshots."""
    all_potential_sections = section_locator.all()
    print(f"\n--- Filtering {len(all_potential_sections)} potential sections ---")
    valid_sections = []
    for i, locator in enumerate(all_potential_sections):
        try:
            if not locator.is_visible(): continue
            box = locator.bounding_box()
            if box and box['height'] >= MIN_SECTION_HEIGHT:
                valid_sections.append(locator)
        except Exception:
            continue
    
    if not valid_sections:
        print("No valid sections remained after filtering.")
        return

    print(f"\n--- Capturing {len(valid_sections)} valid sections ---")
    os.makedirs(output_dir, exist_ok=True)
    for i, locator in enumerate(valid_sections):
        screenshot_path = os.path.join(output_dir, f"section_{i+1:02d}.jpg")
        try:
            locator.scroll_into_view_if_needed()
            time.sleep(0.2)
            print(f"Capturing section {i+1} to {screenshot_path}")
            locator.screenshot(path=screenshot_path, quality=70, type="jpeg" )
        except Exception as e:
            print(f"Could not capture section {i+1}. Error: {e}")

def extract_table_data_from_page_as_images(page, output_path):
        page.set_viewport_size({"width": 1280, "height": 1024})
        page.screenshot(path=f"{output_path}/original_screenshot.jpeg", quality=70, type="jpeg" )
        # Find the best selector for the sections on the main page
        section_locator = find_best_section_locator(page)
        if section_locator:
            filter_and_capture_sections(section_locator, output_path)
        else:
            print("Could not find any sections to capture.")

        print("\n✅ Capture complete!")
    
    
def extract_table_data_as_images(url, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Navigating to {url}...")
        # Use 'networkidle' to be sure all content and styles are loaded.
        page.goto(url, wait_until="networkidle")
        extract_table_data_from_page_as_images(page, output_path)
        browser.close()