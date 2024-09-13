import json
import requests
import os
import traceback
from typing import Dict, Any, List, Tuple
from glob import glob

# Replace with your FHIR server URL
FHIR_SERVER_URL = "http://localhost:8080/fhir"

def load_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as file:
        return json.load(file)

def send_to_fhir_server(resource_type: str, data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    url = f"{FHIR_SERVER_URL}/{resource_type}"
    headers = {
        'Content-Type': 'application/fhir+json',
        'Accept': 'application/fhir+json'
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code >300:
        print(response.text)
    response.raise_for_status()
    return response.json()['id'], response.json()

def retrieve_from_fhir_server(resource_type: str, resource_id: str) -> Dict[str, Any]:
    url = f"{FHIR_SERVER_URL}/{resource_type}/{resource_id}"
    headers = {'Accept': 'application/fhir+json'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def find_missing_fields(original: Dict[str, Any], retrieved: Dict[str, Any], path: str = "") -> List[str]:
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

def compare_json(original: Dict[str, Any], retrieved: Dict[str, Any]) -> Tuple[bool, List[str]]:
    # Remove metadata fields that might have been added by the server
    fields_to_ignore = ['id', 'meta', 'lastUpdated']
    for field in fields_to_ignore:
        original.pop(field, None)
        retrieved.pop(field, None)
    
    missing_fields = find_missing_fields(original, retrieved)
    return original == retrieved, missing_fields

def test_fhir_resource(resource_type: str, file_path: str) -> bool:
    print(f"Testing {resource_type} resource from file: {file_path}")
    
    try:
        # Load original JSON
        original_data = load_json(file_path)
        
        # Send to FHIR server
        resource_id, server_response = send_to_fhir_server(resource_type, original_data)
        print(f"Resource sent to FHIR server. ID: {resource_id}")
        # print("Server response:", json.dumps(server_response, indent=2))
        
        # Retrieve from FHIR server
        retrieved_data = retrieve_from_fhir_server(resource_type, resource_id)
        print("Resource retrieved from FHIR server.")
        # print("Retrieved data:", json.dumps(retrieved_data, indent=2))
        
        # Compare original and retrieved data
        is_equal, missing_fields = compare_json(original_data, retrieved_data)
        
        print(f"Data integrity maintained: {is_equal}")
        if not is_equal:
            print("Missing fields:")
            for field in missing_fields:
                print(f"  - {field}")
        
        return is_equal
    
    except Exception as e:
        print(f"Error occurred while processing {file_path}:")
        print(traceback.format_exc())
        return False

def test_resource_batch(resource_type: str, directory: str) -> bool:
    print(f"\nTesting batch of {resource_type} resources:")
    all_passed = True
    file_pattern = os.path.join(directory, f"{resource_type}*.json")
    for file_path in glob(file_pattern):
        if not test_fhir_resource(resource_type, file_path):
            all_passed = False
    return all_passed

def main():
    resources = {
        "Practitioner": "./resources/practitioner/",
        "Patient": "./resources/patient/",
        "Condition": "./resources/condition/",
        "Organization": "./resources/organization/",
        "Provenance": "./resources/provenance/",
        "Linkage": "./resources/linkage/"
    }
    
    all_tests_passed = True
    
    for resource_type, directory in resources.items():
        if not test_resource_batch(resource_type, directory):
            all_tests_passed = False
    
    if all_tests_passed:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed. Please check the output above for details.")

if __name__ == "__main__":
    main()