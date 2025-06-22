import json
import os
import random
import string
from deepdiff import DeepDiff


def generate_random_prefix(length=8):
    """Generates a random string of characters and digits for a filename prefix."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))




def compare_json_files_deepdiff(file_paths: list) -> str:
    """
    Compares the content of multiple JSON files using DeepDiff for a robust,
    order-agnostic comparison of lists.

    Args:
        file_paths: A list of paths to the JSON files to compare.

    Returns:
        "SUCCESS" if all files have semantically identical content.
        "FAILED" if there is a mismatch, a file is missing, or a file is not valid JSON.
        "NO_COMPARISON" if fewer than two files are provided.
    """
    if len(file_paths) < 2:
        print("Warning: Less than two files provided. No comparison performed.")
        return "NO_COMPARISON"

    try:
        # Load the first file as the reference
        reference_path = file_paths[0]
        print(f"Using '{os.path.basename(reference_path)}' as the reference.")
        with open(reference_path, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Reference file not found at '{reference_path}'")
        return "FAILED"
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from reference file '{reference_path}'")
        return "FAILED"

    # Compare all other files against the reference
    for other_path in file_paths[1:]:
        try:
            print(f"Comparing with '{os.path.basename(other_path)}'...")
            with open(other_path, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            # The core comparison logic using DeepDiff
            # ignore_order=True is crucial for comparing lists of objects
            # where order doesn't matter (e.g., table rows).
            diff = DeepDiff(reference_data, current_data, ignore_order=True)
            
            # An empty DeepDiff object means there are no differences.
            if diff:
                print(f"--- MISMATCH DETECTED ---")
                print(f"File '{os.path.basename(other_path)}' does not match the reference.")
                print("Detailed differences:")
                # .pretty() gives a human-readable report of the changes
                print(diff.pretty())
                return "FAILED"

        except FileNotFoundError:
            print(f"Error: Comparison file not found at '{other_path}'")
            return "FAILED"
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from comparison file '{other_path}'")
            return "FAILED"

    print("--- ALL FILES MATCH ---")
    return "SUCCESS"
