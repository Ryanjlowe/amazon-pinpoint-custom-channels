import boto3, json, os, logging

sqs = boto3.client('sqs')

queue_url = os.environ['SQS_QUEUE_URL']

# This function can be used within an Amazon Pinpoint Campaign or Amazon Pinpoint Journey.

def lambda_handler(event, context):

    logging.getLogger().setLevel('INFO')
    # print the payload the Lambda was invoked with
    logging.info(event)
    logging.info(queue_url)

    if 'Endpoints' not in event:
        return "Function invoked without endpoints."
    # A valid invocation of this channel by the Pinpoint Service will include Endpoints in the event payload

    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event)
        )
    except Exception as e:
        logging.error(e)
        logging.error("Error trying to enqueue the voice message to SQS")

    logging.info("Complete")
    return "Complete"
