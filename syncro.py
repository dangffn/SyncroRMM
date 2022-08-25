import sys
import requests
import csv
import logging
import argparse


"""
This script interacts with the Syncro RMM API
Primarily used for exporting Syncro contacts to a CSV file
Syncro currently (08-25-2022) does not have any options of exporting contacts

To use this script you will need the following:
    - Subdomain for your Syncro account
    - API key created in the Admin page of your Syncro account
        This API key will need permissions to both contacts and customers
"""


logging.basicConfig(level=logging.INFO)


class Syncro:

    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

        # authorization headers for the authenticated API endpoints
        self.headers = {
            "Authorization": f"{api_key}",
            "Accept": "application/json"
        }

    def _get_page(self, url, parameters=None, page=1) -> [dict, int, int]:
        """
        Get a single page from an API endpoint

        :param url: The full URL to query
        :param parameters: Query parameters for the API request
        :param page: Page number to get
        :return: Data retrieved from the API response, number of the current page, number of total pages
        """
        if not parameters: parameters = {}
        parameters["page"] = page

        logging.debug(f"Fetching --> {url} [page={page}]")
        response = requests.get(url, headers=self.headers, json=parameters)
        if response.status_code == 200:
            # successful response code
            data = response.json()
            page = data.get("meta", {}).get("page", -1)
            total_pages = data.get("meta", {}).get("total_pages", -1)
            return data, page, total_pages

        else:
            # unsuccessful response code
            raise APIError(response)

    def _get_all(self, url_prefix, parameters=None) -> dict:
        """
        Get all pages from a paginated API endpoint

        :param url_prefix: The endpoint prefix to append to the base_url
        :param parameters: Query parameters for the API request
        :return: Data retrieved from the API response
        """
        url = self.base_url + url_prefix

        data, page, total_pages = self._get_page(url, parameters=parameters, page=1)
        yield data

        while page < total_pages:
            data, page, total_pages = self._get_page(url, parameters=parameters, page=page + 1)
            yield data

    def get_headers(self, generator_func):
        """
        Just retrieve the headers from the API request, passing in the generator function to get pages
        This is used for creating the CSV headers for exporting

        :param generator_func: The generator that retrieves pages from the API
        :return: List of keys from the first page of the API response
        """
        page = next(generator_func)
        data = page[0]
        return list(data.keys())

    def all_contacts(self, customer_id=None):
        """
        Generator function to get all of the contacts from Syncro

        :param customer_id: Optional customer ID, if specified only contacts that belong to this customer will be returned
        :return: List of contacts from the API response
        """
        params = dict(customer_id=customer_id)
        for page in self._get_all("/contacts", parameters=params):
            yield page.get("contacts", [])

    def all_customers(self):
        """
        Generator function to get all of the customers from Syncro

        :return: List of customers from the API response
        """
        for page in self._get_all("/customers"):
            yield page.get("customers", [])

    def create_contact(self, **kwargs):
        """
        Create a contact in Syncro
        Possible fields for contacts:
            - "customer_id", "name", "address1", "address2", "city", "state", "zip", "email", "phone", "mobile", "notes"

        :param kwargs: Data containing parameters for the new contact
        :return: True if the contact was created successfully
        """
        url = self.base_url + "/contacts"
        # filter only appropriate values per the spec
        # https://api-docs.syncromsp.com/#/Contact/post_contacts
        data = {key: val for key, val in kwargs.items() if key in ["customer_id", "name", "address1", "address2", "city", "state", "zip", "email", "phone", "mobile", "notes"]}
        response = requests.post(url, headers=self.headers, data=data)
        if response.status_code == 200:
            return True
        else:
            raise APIError(response)


class APIError(Exception):
    def __init__(self, response):
        super().__init__(f"Error Response from Syncro [{response.status_code}] ({response.reason})")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Export contacts from Syncro RMM to a CSV file")
    parser.add_argument("-k", "--api-key", required=True, help="Your Syncro API key")
    parser.add_argument("-s", "--subdomain", required=True, help="Your Syncro subdomain (the part before syncromsp.com, ie. {subdomain}.syncromsp.com)")
    parser.add_argument("-o", "--outfile", required=True, help="The path to the csv file to save to (overwrites existing files)")
    parser.add_argument("-c", "--customer-id", help="An optional customer ID, if specified, only contacts for this customer ID will be exported")

    args = parser.parse_args()

    api = Syncro(f"https://{args.subdomain}.syncromsp.com/api/v1", args.api_key)

    try:
        fieldnames = api.get_headers(api.all_contacts())

        if not args.customer_id:
            logging.info("Downloading all contacts in Syncro")
        else:
            logging.info(f"Downloading all contacts for customer {args.customer_id} in Syncro")

        with open(args.outfile, "w") as outfile:
            csvwriter = csv.DictWriter(outfile, fieldnames=fieldnames)
            csvwriter.writeheader()
            for contacts_page in api.all_contacts(customer_id=args.customer_id):
                csvwriter.writerows(contacts_page)

        print(f"Contacts saved to {args.outfile}")

    except APIError as e:
        logging.error(f"There was an error loading the contacts from the Syncro API ({e})")
        sys.exit(1)

    except Exception as e:
        logging.error(f"An unknown error occurred ({e})")
        sys.exit(1)
