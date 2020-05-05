from time import sleep
import boto3, json, os, logging, datetime

connect = boto3.client('connect')
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
        contact_flow_id = pinpoint_event['contact_flow_id']
        instance_id = pinpoint_event['instance_id']
        queue_id = pinpoint_event['queue_id']
        message = pinpoint_event['message']

        custom_events_batch = {}
        # Gather events to emit back to Pinpoint for reporting

        logging.info(endpoint_id)
        logging.info(message)
        logging.info(contact_flow_id)
        logging.info(instance_id)
        logging.info(queue_id)

        try:

            response = connect.start_outbound_voice_contact(
                DestinationPhoneNumber=address,
                ContactFlowId=contact_flow_id,
                InstanceId=instance_id,
                QueueId=queue_id,
                Attributes={
                    'Message': message
                }
            )
            logging.info(response)

            custom_events_batch[endpoint_id] = create_success_custom_event(endpoint_id, campaign_id, message)

        except Exception as e:
            logging.error(e)
            logging.error("Error trying to send a Pinpoint Connect message")

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
        # Sleep 3 seconds between calls to avoid rate limiting


    logging.info("Complete")
    return "Complete"

def create_success_custom_event(endpoint_id, campaign_id, message):
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['voice_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'connect.success',
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
        'EventType': 'connect.failure',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'campaign_id': campaign_id,
            'error': (error[:195] + '...') if len(error) > 195 else error
        }
    }
    return custom_event
