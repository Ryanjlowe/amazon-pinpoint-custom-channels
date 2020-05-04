from time import sleep
import boto3, json, os, logging, datetime

pinpoint_sms_voice = boto3.client('pinpoint-sms-voice')
pinpoint_client = boto3.client('pinpoint')

pinpoint_long_codes = os.environ['PINPOINT_LONG_CODES'].split(',')

# This function can be used within an Amazon Pinpoint Campaign or Amazon Pinpoint Journey.

def lambda_handler(event, context):

    logging.getLogger().setLevel('INFO')
    # print the payload the Lambda was invoked with from SQS
    logging.info(event)

    for record in event['Records']:
        payload=record["body"]
        pinpoint_event = json.loads(payload)

        if 'Endpoints' not in pinpoint_event:
            return "Function invoked without endpoints."
        # A valid invocation of this channel by the Pinpoint Service will include Endpoints in the pinpoint_event payload

        endpoints = pinpoint_event['Endpoints']
        pinpoint_project_id = pinpoint_event['ApplicationId']

        custom_events_batch = {}
        # Gather events to emit back to Pinpoint for reporting

        i = 0
        for endpoint_id in endpoints:

            long_code = pinpoint_long_codes[i % len(pinpoint_long_codes)]
            i += 1
            endpoint_profile = endpoints[endpoint_id]
            # the endpoint profile contains the entire endpoint definition.
            # Attributes and UserAttributes can be interpolated into your message for personalization.

            address = endpoints[endpoint_id]['Address']
            # address is expected to be a Phone Number e.g. +15555555555.

            message = "Hello World!  -Pinpoint Voice Channel"
            # construct your message here.  You have access to the endpoint profile to personalize the message with Attributes.
            # e.g. message = "Hello {name}!  -Pinpoint Voice Channel".format(name=endpoint_profile["Attributes"]["FirstName"])

            logging.info(endpoint_id)
            logging.info(endpoint_profile)
            logging.info(address)
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

                custom_events_batch[endpoint_id] = create_success_custom_event(endpoint_id, pinpoint_event['CampaignId'], message)

            except Exception as e:
                logging.error(e)
                logging.error("Error trying to send a Pinpoint Voice message")

                custom_events_batch[endpoint_id] = create_failure_custom_event(endpoint_id, pinpoint_event['CampaignId'], e)

            if i % len(pinpoint_long_codes):
                sleep(3)
            # Sleep 3 seconds between calls on the same long code avoid rate limiting

    try:
        # submit events back to Pinpoint for reporting
        put_events_result = pinpoint_client.put_events(
            ApplicationId=pinpoint_event['ApplicationId'],
            EventsRequest={
                'BatchItem': custom_events_batch
            }
        )
        logging.info(put_events_result)
    except Exception as e:
        logging.error(e)
        logging.error("Error trying to send custom events to Pinpoint")


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
            'message': message
        }
    }
    return custom_event

def create_failure_custom_event(endpoint_id, campaign_id, e):
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['voice_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'voice.failure',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'campaign_id': campaign_id,
            'error': repr(e)
        }
    }
    return custom_event
