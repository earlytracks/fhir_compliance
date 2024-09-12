import json
import requests
import os
from typing import Dict, Any

# Replace with your FHIR server URL
FHIR_SERVER_URL = "http://localhost:8080/fhir"

def load_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as file:
        return json.load(file)

def send_to_fhir_server(resource_type: str, data: Dict[str, Any]) -> str:
    url = f"{FHIR_SERVER_URL}/{resource_type}"
    headers = {
        'Content-Type': 'application/fhir+json',
        'Accept': 'application/fhir+json'
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()['id']  # Assuming the server returns the resource ID

def retrieve_from_fhir_server(resource_type: str, resource_id: str) -> Dict[str, Any]:
    url = f"{FHIR_SERVER_URL}/{resource_type}/{resource_id}"
    headers = {'Accept': 'application/fhir+json'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def find_missing_fields(original: Dict[str, Any], retrieved: Dict[str, Any], path: str = "") -> list:
    missing_fields = []
    for key, value in original.items():
        new_path = f"{path}.{key}" if path else key
        if key not in retrieved:
            missing_fields.append(new_path)
        elif isinstance(value, dict) and isinstance(retrieved.get(key), dict):
            missing_fields.extend(find_missing_fields(value, retrieved[key], new_path))
        elif isinstance(value, list) and isinstance(retrieved.get(key), list):
            for i, item in enumerate(value):
                if i < len(retrieved[key]):
                    if isinstance(item, dict):
                        missing_fields.extend(find_missing_fields(item, retrieved[key][i], f"{new_path}[{i}]"))
                else:
                    missing_fields.append(f"{new_path}[{i}]")
    return missing_fields

def compare_json(original: Dict[str, Any], retrieved: Dict[str, Any]) -> tuple:
    # Remove metadata fields that might have been added by the server
    fields_to_ignore = ['id', 'meta', 'lastUpdated']
    for field in fields_to_ignore:
        original.pop(field, None)
        retrieved.pop(field, None)
    
    missing_fields = find_missing_fields(original, retrieved)
    return original == retrieved, missing_fields

def test_fhir_resource(resource_type: str, file_path: str) -> bool:
    print(f"Testing {resource_type} resource:")
    
    # Load original JSON
    original_data = load_json(file_path)
    
    try:
        # Send to FHIR server
        resource_id = send_to_fhir_server(resource_type, original_data)
        print(f"Resource sent to FHIR server. ID: {resource_id}")
        
        # Retrieve from FHIR server
        retrieved_data = retrieve_from_fhir_server(resource_type, resource_id)
        print("Resource retrieved from FHIR server.")
        
        # Compare original and retrieved data
        is_equal, missing_fields = compare_json(original_data, retrieved_data)
        
        print(f"Data integrity maintained: {is_equal}")
        if not is_equal:
            print("Missing fields:")
            for field in missing_fields:
                print(f"  - {field}")
        
        return is_equal
    
    except requests.RequestException as e:
        print(f"Error occurred: {e}")
        return False

def main():
    resources = {
        "Practitioner": "./resources/Practitioner-practitioner1.json",
        "Condition": "./resources/Condition-problem-1.json",
        "Condition": "./resources/Condition-problem-2.json",
        "Provenance": "./resources/Provenance-provenance-1.json",
        "Linkage": "./resources/Linkage-LinkageExample.json"
    }
    
    all_tests_passed = True
    
    for resource_type, file_path in resources.items():
        if not test_fhir_resource(resource_type, file_path):
            all_tests_passed = False
    
    if all_tests_passed:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed. Please check the output above for details.")

if __name__ == "__main__":
    main()