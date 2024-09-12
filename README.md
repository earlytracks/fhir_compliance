# fhir_compliance
This repository aim to check wether the interface used by hospital are returning the fhir implementation expected by EarlyTracks.

## First steps:
- Make sure your fhir endpoint is accessible.
- Add all the examples provided in the `resources` folder.
- In the `main.py`, make sure the naming of the files is reflected in the `main()`.
    - The ordering is important as some resources are relying on other. I.e.: the Practioner is a prerequisite for the Conditions.
- In the `main.py` adapt the url `FHIR_SERVER_URL` to your endpoint url accepting FHIR.

- Run the python script.
- In the terminal, you will see whether:
    - that everything went according to plan.
    - that there are missing fields for all specific resources.