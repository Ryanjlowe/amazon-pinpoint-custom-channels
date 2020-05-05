# See https://developers.google.com/adwords/api/docs/samples/python/remarketing#add-crm-based-user-list

import boto3, json, os, logging, datetime, time
import hashlib
import uuid

user_list_id = os.environ.get('GOOGLE_ADS_USER_LIST_ID')
client_customer_id = os.environ.get('CLIENT_CUSTOMER_ID')
developer_token = os.environ.get('GOOGLE_ADS_DEVELOPER_TOKEN')
client_id = os.environ.get('GOOGLE_ADS_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_ADS_CLIENT_SECRET')
refresh_token = os.environ.get('GOOGLE_ADS_REFRESH_TOKEN')
user_agent = 'PinpointCustomChannel'

# Import appropriate modules from the client library.
from googleads import adwords
from googleads import oauth2
from googleads import common
# Initialize appropriate services.

oauth2_client = oauth2.GoogleRefreshTokenClient(
      client_id, client_secret, refresh_token)

adwords_client = adwords.AdWordsClient(
      developer_token, oauth2_client, user_agent,
      client_customer_id=client_customer_id,
      cache=common.ZeepServiceProxy.NO_CACHE)

user_list_service = adwords_client.GetService('AdwordsUserListService', 'v201809')


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

    members = []

    custom_events_batch = {}
    # Gather events to emit back to Pinpoint for reporting

    for endpoint_id in event['Endpoints']:
        endpoint_profile = event['Endpoints'][endpoint_id]
        # the endpoint profile contains the entire endpoint definition.
        # Attributes and UserAttributes can be interpolated into your message for personalization.

        if endpoint_profile['ChannelType'] == 'EMAIL':
            address = endpoint_profile['Address']

            members.append({'hashedEmail':NormalizeAndSHA256(address)})
            custom_events_batch[endpoint_id] = create_success_custom_event(endpoint_id, campaign_id, user_list_id)


    if len(members) > 0:
        mutate_members_operation = {
            'operand': {
                'userListId': user_list_id,
                'membersList': members
            },
            'operator': 'ADD'
        }

        try:
            # Call Google to add members
            response = user_list_service.mutateMembers([mutate_members_operation])
            logging.info(response)


        except Exception as e:
            logging.error(e)
            logging.error("Error trying to add users to google ads audience")
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


    logging.info("Complete")
    return "Complete"

def NormalizeAndSHA256(s):
  """Normalizes (lowercase, remove whitespace) and hashes a string with SHA-256.

  Args:
    s: The string to perform this operation on.

  Returns:
    A normalized and SHA-256 hashed string.
  """
  return hashlib.sha256(s.strip().lower()).hexdigest()

def create_success_custom_event(endpoint_id, campaign_id, user_list_id):
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['googleads_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'googleads.success',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'campaign_id': campaign_id,
            'user_list_id': user_list_id
        }
    }
    return custom_event

def create_failure_custom_event(endpoint_id, campaign_id, e):
    error = repr(e)
    custom_event = {
        'Endpoint': {},
        'Events': {}
    }
    custom_event['Events']['googleads_%s_%s' % (endpoint_id, campaign_id)] = {
        'EventType': 'googleads.failure',
        'Timestamp': datetime.datetime.now().isoformat(),
        'Attributes': {
            'campaign_id': campaign_id,
            'error': (error[:195] + '...') if len(error) > 195 else error
        }
    }
    return custom_event
