import boto3, json, os, logging, random

sqs = boto3.client('sqs')

queue_url = os.environ['SQS_QUEUE_URL']
contact_flow_id=os.environ['CONNECT_CONTACT_FLOW_ID']
instance_id=os.environ['CONNECT_INSTANCE_ID']
queue_id=os.environ['CONNECT_QUEUE_ID']

# This function can be used within an Amazon Pinpoint Campaign or Amazon Pinpoint Journey.

def lambda_handler(event, context):

    logging.getLogger().setLevel('INFO')
    # print the payload the Lambda was invoked with
    logging.info(event)
    logging.info(queue_url)

    if 'Endpoints' not in event:
        return "Function invoked without endpoints."
    # A valid invocation of this channel by the Pinpoint Service will include Endpoints in the event payload

    for endpoint_id in event['Endpoints']:
        endpoint_profile = event['Endpoints'][endpoint_id]
        # the endpoint profile contains the entire endpoint definition.
        # Attributes and UserAttributes can be interpolated into your message for personalization.

        address = endpoint_profile['Address']
        # address is expected to be a Phone Number e.g. +15555555555.

        message = "Hello World!  -Pinpoint Connect Channel"
        # construct your message here.  You have access to the endpoint profile to personalize the message with Attributes.
        # e.g. message = "Hello {name}!  -Pinpoint Voice Channel".format(name=endpoint_profile["Attributes"]["FirstName"])


        msg = {
            'endpoint_id': endpoint_id,
            'campaign_id': event['CampaignId'],
            'application_id': event['ApplicationId'],
            'contact_flow_id': contact_flow_id,
            'instance_id': instance_id,
            'queue_id': queue_id,
            'message': message,
            'address': address
        }

        try:
            response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(msg),
                MessageDeduplicationId="%s-%s" % (event['CampaignId'], endpoint_id),
                MessageGroupId=queue_id
            )
        except Exception as e:
            logging.error(e)
            logging.error("Error trying to enqueue the connect message to SQS")

    logging.info("Complete")
    return "Complete"
