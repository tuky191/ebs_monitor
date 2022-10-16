
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.model.event_create_request import EventCreateRequest
import time
import boto3
from dotenv import load_dotenv
import logging
import json
from datetime import datetime, timedelta, timezone
from pprint import pprint
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

load_dotenv()


def get_volumes():
    client = boto3.client('ec2', region_name='us-east-1')
    response = client.describe_volumes(
        Filters=[
            {
                'Name': 'volume-type',
                'Values': [
                    'io1',
                    'io2'
                ]
            },
        ]
    )
    return response["Volumes"]


def send_notification(kwargs):
    body = EventCreateRequest(
        **kwargs
    )
    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api_instance = EventsApi(api_client)
        response = api_instance.create_event(body=body)
        logging.info("%s", response)


if __name__ == "__main__":
    volumes = get_volumes()

    if len(volumes) > 0:
        current_time = datetime.now(timezone.utc)
        result = [{"VolumeId": volume["VolumeId"], "VolumeType": volume["VolumeType"], "Iops": volume["Iops"], "Size": volume["Size"], "CreateTime": volume["CreateTime"].strftime("%Y-%m-%dT%H:%M:%SZ")}
                  for volume in volumes if volume["CreateTime"] > current_time - timedelta(hours=8)]
        if len(result) > 0:
            logging.info("Found io1/io2 volumes: %s", result)
            send_notification({
                "title": "Found io1 or io2 volumes existing longer then 8 hours",
                "text": json.dumps(result),
                "tags": ["app:ebs_monitor"],
                "alert_type": "warning",
            })
        else:
            logging.info("No io1/io2 volumes found")
