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

import logging, json, phonenumbers
from salesforce import Salesforce
from datetime import datetime, timedelta
from sf_util import parse_date

logger = logging.getLogger()

def removekey(d, key):
    r = dict(d)
    del r[key]
    return r

def lambda_handler(event, context):
  logger.info("event: %s" % json.dumps(event))

  sf = Salesforce()
  sf.sign_in()

  sf_operation = str(event['Details']['Parameters']['sf_operation'])
  parameters = dict(event['Details']['Parameters'])
  del parameters['sf_operation']
  event['Details']['Parameters'] = parameters

  if(sf_operation == "lookup"):
    resp = lookup(sf=sf, **event['Details']['Parameters'])
  elif (sf_operation == "create"):
    resp = create(sf=sf, **event['Details']['Parameters'])
  elif (sf_operation == "update"):
    resp = update(sf=sf, **event['Details']['Parameters'])
  elif (sf_operation == "phoneLookup"):
    resp = phoneLookup(sf, event['Details']['Parameters']['sf_phone'], event['Details']['Parameters']['sf_fields'])
  else:
    msg = "sf_operation unknown"
    logger.error(msg)
    raise Exception(msg)
  
  logger.info("result: %s" % resp)
  return resp

def lookup(sf, sf_object, sf_fields, **kwargs):
  where = " AND ".join([where_parser(*item) for item in kwargs.items()])
  query = "SELECT %s FROM %s WHERE %s" % (sf_fields, sf_object, where)
  records = sf.query(query=query)
  count = len(records)
  result = records[0] if count > 0 else {}
  result['sf_count'] = count
  return result
    
def where_parser(key, value):
  if key.lower() in ['mobilephone', 'homephone']:
    return "%s LIKE '%%%s%%%s%%%s%%'" % (key, value[-10:-7], value[-7:-4], value[-4:])
    
  if "%" in value:
    return "%s LIKE '%s'" % (key, value)

  return "%s='%s'" % (key, value)

def create(sf, sf_object, **kwargs):
  data = {k:parse_date(v) for k,v in kwargs.items()}
  return {'Id':sf.create(sobject=sf_object, data=data)}

def update(sf, sf_object, sf_id, **kwargs):
  data = {k:parse_date(v) for k,v in kwargs.items()}
  return {'Status':sf.update(sobject=sf_object, sobj_id=sf_id, data=data)}

def phoneLookup(sf, phone, sf_fields):
  phone_national = str(phonenumbers.parse(phone, None).national_number)

  params = {
    'q':phone_national,
    'sobject':'Contact',
    'Contact.fields':sf_fields 
  }
  records = sf.parameterizedSearch(params=params)

  count = len(records)
  
  if (count > 0):
    result = records[0]   
  else:
    result = {}

  result['sf_count'] = count
  return result

