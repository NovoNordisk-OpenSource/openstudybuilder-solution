# This locust load test script will simulate users accessing endpoints in the SB API.
#
# Each API endpoint invocation is represented by a `@task(weight)` annotation,
# where `weight`` represents relative frequency of random invocations of different endpoints.

import random

import requests
from locust import HttpUser, between, events, task

from tests.utils import Params, get_all_endpoints, get_big_study_id, get_random_endpoint, pretty_print_endpoint

PAGE_SIZE = 10


# pylint: disable=unused-argument
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Test session starting...")

    if Params.AUTO_DETECT_BIG_STUDY:
        get_big_study_id()

    if Params.PREFETCH_ENDPOINTS:
        host = Params.CONSUMER_API_BASE_URL if Params.TARGET_CONSUMER_API else Params.API_BASE_URL
        for url, params in get_all_endpoints(Params.TARGET_CONSUMER_API):
            print(f"Pre-fetching {pretty_print_endpoint(host, url, params)}")
            res = requests.get(f"{host}{url}", headers=Params.API_HEADERS, params=params, verify=False, timeout=300)
            print(f" => {res.status_code}")


class StudyBuilder(HttpUser):
    host = Params.CONSUMER_API_BASE_URL if Params.TARGET_CONSUMER_API else Params.API_BASE_URL

    wait_time = between(1, 3)

    def on_start(self):
        print("==== User joins =====")
        # start by waiting so that the simulated users
        # won't all arrive at the same time
        self.wait()

    @task(100)
    def get_random(self):
        """Issues GET request to a random endpoint"""
        url, params = get_random_endpoint(Params.TARGET_CONSUMER_API)
        self.client.get(url, headers=Params.API_HEADERS, params=params, verify=False)

    @task(0 if Params.TARGET_CONSUMER_API else 30)
    def clear_caches(self):
        url = "/admin/caches"
        self.client.delete(url, headers=Params.API_HEADERS, verify=False)

    @task(0)
    def get_study_compounds(self):
        url = f"/studies/{Params.STUDY_ID}/study-compounds"
        self.client.get(url, headers=Params.API_HEADERS, verify=False)

    @task(0)
    def get_library_compounds(self):
        # url = '/concepts/compounds?page_number=1&page_size=10&total_count=true&filters=%7B"*"+:%7B+"v":+[""]%7D%7D&sort_by=%7B"name":true%7D'
        url = f"/concepts/compounds?page_number=1&page_size={PAGE_SIZE}&total_count=true"
        self.client.get(url, headers=Params.API_HEADERS, verify=False)

    @task(0)
    def get_ct_terms(self):
        page_number = random.randint(1, 150)
        url = f"/ct/codelists?page_number={page_number}&page_size={PAGE_SIZE}&total_count=true"
        self.client.get(url, headers=Params.API_HEADERS, verify=False)

    @task(0)
    def get_activities(self):
        page_number = random.randint(1, 150)
        url = f'/concepts/activities/activities?page_number={page_number}&page_size={PAGE_SIZE}&total_count=true&sort_by={{"activity_group.name":false}}'
        self.client.get(url, headers=Params.API_HEADERS, verify=False)
