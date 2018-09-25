"""
You must have an AWS account to use the Amazon Connect CTI Adapter.
Downloading and/or using the Amazon Connect CTI Adapter is subject to the terms of the AWS Customer Agreement,
AWS Service Terms, and AWS Privacy Notice.

© 2017, Amazon Web Services, Inc. or its affiliates. All rights reserved.

NOTE:  Other license terms may apply to certain, identified software components
contained within or distributed with the Amazon Connect CTI Adapter if such terms are
included in the LibPhoneNumber-js and Salesforce Open CTI. For such identified components,
such other license terms will then apply in lieu of the terms above.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json, logging, os
from botocore.vendored import requests
from sf_util import get_arg

logger = logging.getLogger()

class Salesforce:

  def __init__(self):

    self.version=get_arg(os.environ, "SF_VERSION")
    self.host=get_arg(os.environ, "SF_HOST")
    self.consumer_key=get_arg(os.environ, "SF_CONSUMER_KEY") 
    self.consumer_secret=get_arg(os.environ, "SF_CONSUMER_SECRET")
    self.username=get_arg(os.environ, "SF_USERNAME")
    self.password=get_arg(os.environ, "SF_PASSWORD") + get_arg(os.environ, "SF_ACCESS_TOKEN")

    self.login_host = self.host
    self.request = Request()
    self.access_token = None
    self.auth_data = {
      'grant_type': 'password',
      'client_id': self.consumer_key,
      'client_secret': self.consumer_secret,
      'username': self.username,
      'password': self.password
    }
    if get_arg(os.environ, "SF_PRODUCTION").lower() == "true":
      self.set_production()

  def set_production(self):
    self.login_host = 'https://login.salesforce.com'

  def sign_in(self):
    logger.debug("Salesforce: Sign in")
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    resp = self.request.post(url=self.login_host+"/services/oauth2/token", params=self.auth_data, headers=headers)
    data = resp.json()
    self.access_token = data['access_token']
    self.host = data['instance_url']
    self.headers = { 
      'Authorization': 'Bearer %s' % self.access_token,
      'Content-Type': 'application/json'
    }

  def search(self, query):
    logger.debug("Salesforce: Search")
    url = '%s/services/data/%s/search' % (self.host, self.version)
    resp = self.request.get(url=url, params={'q':query}, headers=self.headers)
    return resp.json()['searchRecords']

  def query(self, query):#TODO: create generator that takes care of subsequent request for more than 200 records
    logger.debug("Salesforce: Query")
    url = '%s/services/data/%s/query' % (self.host, self.version)
    resp = self.request.get(url=url, params={'q':query}, headers=self.headers)
    data = resp.json()
    for record in data['records']:
        del record['attributes']
    return data['records']

  def parameterizedSearch(self, params):#TODO: create generator that takes care of subsequent request for more than 200 records
    logger.debug("Salesforce: Query")
    url = '%s/services/data/%s/parameterizedSearch' % (self.host, self.version)
    resp = self.request.get(url=url, params=params, headers=self.headers)
    data = resp.json()

    for record in data['searchRecords']:
        del record['attributes']
    return data['searchRecords']

  def update(self, sobject, sobj_id, data):
    logger.debug("Salesforce: Update")
    url = '%s/services/data/%s/sobjects/%s/%s' % (self.host, self.version, sobject, sobj_id)
    resp = self.request.patch(url=url, data=data, headers=self.headers)
    return resp.status_code

  def update_by_external(self, sobject, field, sobj_id, data):
    logger.debug("Salesforce: Update by external")
    url = '%s/services/data/%s/sobjects/%s/%s/%s' % (self.host, self.version, sobject, field, sobj_id)
    self.request.patch(url=url, data=data, headers=self.headers)

  def create(self, sobject, data):
    logger.debug("Salesforce: Create")
    url = '%s/services/data/%s/sobjects/%s' % (self.host, self.version, sobject)
    resp = self.request.post(url=url, data=data, headers=self.headers)
    return resp.json()['id']

  def delete(self, sobject, sobject_id):
    logger.debug("Salesforce: Delete")
    url = '%s/services/data/%s/sobjects/%s/%s' % (self.host, self.version, sobject, sobject_id)
    resp = self.request.delete(url=url, headers=self.headers)

  def is_authenticated(self):
    return self.access_token and self.host

class Request:
  def post(self, url, headers, data=None, params=None):
    logger.debug("POST Requests:\nurl=%s\ndata=%s\nparams=%s" % (url, data, params))
    r = requests.post(url=url, data=json.dumps(data), params=params, headers=headers)
    logger.debug("Response: %s" % r.text)
    return __check_resp__(r)

  def delete(self, url, headers):
    logger.debug("DELETE Requests:\nurl=%s" % url)
    r = requests.delete(url=url, headers=headers)
    logger.debug("Response: %s" % r.text)
    return __check_resp__(r)

  def patch(self, url, data, headers):
    logger.debug("PATCH Requests:\nurl=%s\ndata=%s" % (url, data))
    r = requests.patch(url=url, data=json.dumps(data), headers=headers)
    logger.debug("Response: %s" % r.text)
    return __check_resp__(r)

  def get(self, url, params, headers):
    logger.debug("GET Requests:\nurl=%s\nparams=%s" % (url, params))
    r = requests.get(url=url, params=params, headers=headers)
    logger.debug("Response: %s" % r.text)
    return __check_resp__(r)

def __check_resp__(resp):
  if resp.status_code // 100 == 2: 
    return resp
  
  data = resp.json()
  if 'error' in data:
    msg = "%s: %s" % (data['error'], data['error_description'])
    logger.error(msg)
    raise Exception(msg)
  
  if isinstance(data, list):
    for error in data:
      if 'message' in error:
        msg = "%s: %s" % (error['errorCode'], error['message'])
        logger.error(msg)
        raise Exception(msg)

  msg = "request returned status code: %d" % resp.status_code
  logger.error(msg)
  raise Exception(msg)