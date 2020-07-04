# Genesis Health

## Project Summary

Genesis Health manufactures devices for self-testing blood glucose levels.  The results of those tests are uploaded to the Genesis Health servers, where they are processed, stored, and shared with third parties.  This application contains all of the services necessary for receiving readings as well as the web portal used by patients, caregivers, and administrators to interact with that data.

## Development Setup

### Prerequisites

- Python 3.8 (should be available at command line as `python3.8`)
- Postgres Server (installed and running locally)
- An SSH Key configured to use with your GitHub account, which has access to the pronym-inc organization.

### Getting environment setup
You should be able to get started with a few commands.

```
$ git clone git@github.com:pronym-inc/genesishealth.git
Cloning into genesishealth ...
...
$ cd genesishealth
$ install/setup.sh
Creating database...
...
```

### Running the web server
A `manage.py` script is provided in the root of the directory which can be used for interacting with the Django application.
To run the webserver:
```
$ ./manage.py runserver
```

### Running tests
##### Unit Tests
```
$ venv/bin/pytest genesishealth/tests
```
##### Integration Tests
```
$ venv/bin/pytest genesishealth/integration_tests
```