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

import logging
from datetime import datetime, timedelta

logger = logging.getLogger()

def parse_date(value, date=datetime.now()):
    if "|" not in value:
        return value

    value_raw = value.split("|")
    delta_raw = value_raw[0].strip()
    format_raw = value_raw[1].strip()
    delta = timedelta()

    if format_raw not in formats:
      msg = "Supported formats are 'date', 'time' and 'datetime', example '2h|date'"
      logger.error(msg)
      raise Exception(msg)

    if len(delta_raw) > 0:
      delta_value = delta_raw[:-1] 
      delta_type = delta_raw[-1].lower()
      
      if delta_type not in timedeltas:
        msg = "Supported delta types are 'd' for days, 'h' for hours and 'm' for minutes, example '2h|date'"
        logger.error(msg)
        raise Exception(msg)
      
      delta = timedeltas[delta_type](delta_value)

    return (date+delta).strftime(formats[format_raw])

def split_bucket_key(location):
  bucketIndex = location.index('/')
  bucket = location[:bucketIndex]
  key = location[bucketIndex+1:]
  return (bucket, key)

def get_arg(kwargs, name):
  if name not in kwargs:
    msg = "'%s' enviroment variable is missing"
    logger.error(msg)
    raise Exception(msg)
  return kwargs[name]

formats = {
    "datetime":"%Y-%m-%dT%H:%M:%SZ",
    "date":"%Y-%m-%d",
    "time":"%H:%M:%S"
}

timedeltas = {
    "w":lambda v: timedelta(weeks=int(v)),
    "d":lambda v: timedelta(days=int(v)),
    "h":lambda v: timedelta(hours=int(v)),
    "m":lambda v: timedelta(minutes=int(v))
}
