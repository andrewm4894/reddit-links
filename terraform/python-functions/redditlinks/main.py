# -*- coding: utf-8 -*-
import json
import base64
import logging


def dev(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    # get data from event into a dict
    event_data_json = json.loads(base64.b64decode(event['data']).decode('utf-8'))

    # result message
    result_message = f"... hello world ..."
    logging.info(result_message)

    # build response
    response = {
        "statusCode": 200,
        "event": event,
        "context": context,
        "message": event_data_json,
        "result_message": result_message
    }
    logging.info(response)

    return response

