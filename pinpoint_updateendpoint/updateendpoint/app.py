import boto3, json, os, logging, datetime, time

pinpoint_client = boto3.client('pinpoint')
# This function can be used within an Amazon Pinpoint Campaign or Amazon Pinpoint Journey.

def lambda_handler(event, context):

    logging.getLogger().setLevel('INFO')
    # print the payload the Lambda was invoked with
    logging.info(event)

    if 'Endpoints' not in event:
        return "Function invoked without endpoints."
    # A valid invocation of this channel by the Pinpoint Service will include Endpoints in the event payload

    campaign_id = event['CampaignId']
    application_id = event['ApplicationId']

    custom_events_batch = {}
    # Gather events to emit back to Pinpoint for reporting

    for endpoint_id in event['Endpoints']:
        endpoint_profile = event['Endpoints'][endpoint_id]
        # the endpoint profile contains the entire endpoint definition.
        # Attributes and UserAttributes can be interpolated into your message for personalization.

        endpoint_attribute = "PurchaseEventOccured"
        # name of the endpoint attribute to update

        values = ["true"]
        # value for the endpoint attribute, can be an array of strings

        try:
            response = pinpoint_client.update_endpoint(
                ApplicationId=application_id,
                EndpointId=endpoint_id,
                EndpointRequest={
                    'Attributes': {
                        endpoint_attribute: values
                    }
                }
            )
            logging.info(response)

            custom_events_batch[endpoint_id] = create_success_custom_event(endpoint_id, campaign_id, endpoint_attribute, values)

        except Exception as e:
            logging.error(e)
            logging.error("Error trying to update endpoint")
            custom_events_batch[endpoint_id] = create_failure_custom_event(endpoint_id, campaign_id, endpoint_attribute, e)

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


    logging.info("Complete")
    return "Complete"

def create_success_custom_event(endpoint_id, campaign_id, endpoint_attribute, values):
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['updateendpoint_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'update_endpoint.success',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'endpoint_attribute': endpoint_attribute,
            'values': repr(values)
        }
    }
    return custom_event

def create_failure_custom_event(endpoint_id, campaign_id, endpoint_attribute, e):
    error = repr(e)
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['updateendpoint_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'update_endpoint.failure',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'campaign_id': campaign_id,
            'endpoint_attribute': endpoint_attribute,
            'error': (error[:195] + '...') if len(error) > 195 else error
        }
    }
    return custom_event
