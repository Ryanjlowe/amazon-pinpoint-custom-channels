from time import sleep
import boto3, json, os, logging, datetime

pinpoint_sms_voice = boto3.client('pinpoint-sms-voice')
pinpoint_client = boto3.client('pinpoint')


# This function can be used within an Amazon Pinpoint Campaign or Amazon Pinpoint Journey.

def lambda_handler(event, context):

    logging.getLogger().setLevel('INFO')
    # print the payload the Lambda was invoked with from SQS
    logging.info(event)

    for record in event['Records']:
        payload=record["body"]
        pinpoint_event = json.loads(payload)

        endpoint_id = pinpoint_event['endpoint_id']
        application_id = pinpoint_event['application_id']
        campaign_id = pinpoint_event['campaign_id']
        address = pinpoint_event['address']
        long_code = pinpoint_event['long_code']
        message = pinpoint_event['message']

        custom_events_batch = {}
        # Gather events to emit back to Pinpoint for reporting

        logging.info(endpoint_id)
        logging.info(message)
        logging.info(long_code)

        try:

            response = pinpoint_sms_voice.send_voice_message(
                Content={
                    'PlainTextMessage': {
                        'LanguageCode': 'en-US',
                        'Text': message
                    }
                },
                DestinationPhoneNumber=address,
                OriginationPhoneNumber=long_code
            )
            logging.info(response)

            custom_events_batch[endpoint_id] = create_success_custom_event(endpoint_id, campaign_id, message)

        except Exception as e:
            logging.error(e)
            logging.error("Error trying to send a Pinpoint Voice message")

            custom_events_batch[endpoint_id] = create_failure_custom_event(endpoint_id, campaign_id, e)

        try:
            # submit events back to Pinpoint for reporting
            put_events_result = pinpoint_client.put_events(
                ApplicationId=application_id,
                EventsRequest={
                    'BatchItem': custom_events_batch
                }
            )
            logging.info(put_events_result)
        except Exception as e:
            logging.error(e)
            logging.error("Error trying to send custom events to Pinpoint")

        sleep(3)
        # Sleep 3 seconds between calls on the same long code to avoid rate limiting


    logging.info("Complete")
    return "Complete"

def create_success_custom_event(endpoint_id, campaign_id, message):
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['voice_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'voice.success',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'campaign_id': campaign_id,
            'message': (message[:195] + '...') if len(message) > 195 else message
        }
    }
    return custom_event

def create_failure_custom_event(endpoint_id, campaign_id, e):
    error = repr(e)
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['voice_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'voice.failure',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'campaign_id': campaign_id,
            'error': (error[:195] + '...') if len(error) > 195 else error
        }
    }
    return custom_event
