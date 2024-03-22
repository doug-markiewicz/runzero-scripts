# runZero health check scripts

## Overview
These scripts will gather a variety of metrics related to a runZero deployment and export data that can be used to review the health of a deployment. Each script can be run independently or you can use run.py to run through all available scripts. 

## Disclaimer
I'm not really a good coder. Don't judge.

## Requirements
* runZero client ID and secret
* Python 3.10 or newer
* python-dotenv
* requests

## Configuration
1. [Configure client ID and secret in runZero](https://help.runzero.com/docs/leveraging-the-api/#api-client-credentials).
1. Add the following variables to your .env file
  * RUNZERO_BASE_URL = 'https://console.runzero.com/api/v1.0'
  * RUNZERO_CLIENT_ID
  * RUNZERO_CLIENT_SECRET

  NOTE: If you are hosting runZero on-premise, then you will need to update the base URL accordingly. 

## To do list
* Figure out a way to enumerate what connector tasks are configured
* Update explorer script to pull version information from API endpoint instead of metadata file
* Pull names for all UUID things for data exports (e.g. explorers, tasks, templates, etc.)
* Add option to pass arguments vs. configuring a .env file
* Improve formatting of metrics file

## Change log
* 2024-03-22
  * Published initial explorer and task health check scripts