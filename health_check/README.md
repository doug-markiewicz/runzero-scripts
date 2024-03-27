# runZero health check scripts

## Overview
These scripts will gather a variety of metrics related to a runZero deployment and export data that can be used to review the health of a deployment. Each script can be run independently or you can use run.py to run through all available scripts. 

## Disclaimer
I'm not a good coder. Don't judge.

## Requirements
* runZero client ID and secret
* Python 3.10 or newer
* python-dotenv
* requests

## Configuration
1. [Configure client ID and secret in runZero](https://help.runzero.com/docs/leveraging-the-api/#api-client-credentials).
1. Add the following variables to your .env file

    ```
    RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'
    RUNZERO_CLIENT_ID = 'XXX'
    RUNZERO_CLIENT_SECRET = 'XXX'
    ```

  NOTE: If you are hosting runZero on-premise, then you will need to update the base URL accordingly. 

## Known issues
* Connector tasks that are configured to run on local explorers are currently reflected as scan tasks in the metrics.

## Short-term to do list
* Update logic to appropriately identify and report on connector tasks that run on explorers
* Figure out a way to enumerate what connector tasks are configured (e.g. edr, vm, mdm, etc.)
* Update explorer script to pull version information from API endpoint instead of metadata file
* Pull names for all UUID things for data exports (e.g. explorers, tasks, templates, etc.)
* Add basic asset inventory data quality checks (e.g. assets missing OS, mac addr, etc.)
* Add option to pass arguments vs. configuring a .env file
* Add option to run health check on a single organization vs. an account
* ~~Improve formatting of metrics file~~

## Longer term roadmap
* Combine metrics and data exports into a single report (likely a multi-tab .xlsx)

## Change log
* 2024-03-25
  * Updated filenames and path for output files
  * Updated formatting of metrics.txt output file

* 2024-03-22
  * Published initial explorer and task health check scripts