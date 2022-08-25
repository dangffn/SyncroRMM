# Syncro RMM

This is a simple script that interacts with the Syncro RMM for downloading contacts and exporting them to a CSV file

## Installation

```bash
pip install ./requirements.txt
```

## Usage

```bash
usage: syncro.py [-h] -k API_KEY -s SUBDOMAIN -o OUTFILE [-c CUSTOMER_ID]

Export contacts from Syncro RMM to a CSV file

optional arguments:
  -h, --help            show this help message and exit
  -k API_KEY, --api-key API_KEY
                        Your Syncro API key
  -s SUBDOMAIN, --subdomain SUBDOMAIN
                        Your Syncro subdomain (the part before syncromsp.com, ie. {subdomain}.syncromsp.com)
  -o OUTFILE, --outfile OUTFILE
                        The path to the csv file to save to (overwrites existing files)
  -c CUSTOMER_ID, --customer-id CUSTOMER_ID
                        An optional customer ID, if specified, only contacts for this customer ID will be exported

```

To download all Syncro contacts and save them to `contacts.csv`
```bash
python3 syncro.py -k {your-api-key} -s {your-syncro-subdomain} -o ./contacts.csv
```

To download all Syncro contacts for customer id `123456`
```bash
python3 syncro.py -k {your-api-key} -s {your-syncro-subdomain} -c 123456 -o ./contacts-123456.csv
```
