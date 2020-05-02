from time import sleep
import boto3, json, os, logging

pinpoint_sms_voice = boto3.client('pinpoint-sms-voice')

pinpoint_long_codes = os.environ['PINPOINT_LONG_CODES'].split(',')

# This function can be used within an Amazon Pinpoint Campaign or Amazon Pinpoint Journey.
# When invoked by the Amazon Pinpoint service the code below will utilize the DirectMessage API of Twitter to send a user a private twitter message.

def lambda_handler(event, context):

    logging.getLogger().setLevel('INFO')
    # print the payload the Lambda was invoked with
    logging.info(event)

    if 'Endpoints' not in event:
        return "Function invoked without endpoints."
    # A valid invocation of this channel by the Pinpoint Service will include Endpoints in the event payload

    endpoints = event['Endpoints']
    pinpoint_project_id = event['ApplicationId']

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
        # e.g. message = "Hello {name}!  -Pinpoint Twitter Channel".format(name=endpoint_profile["Attributes"]["FirstName"])

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

            # Twitter Direct Message docs - https://developer.twitter.com/en/docs/direct-messages/sending-and-receiving/api-reference/new-event
            # Note: In order for a user to receive a direct message they must have a conversation history with your application or allow direct messages.
            #result = twitter_api.PostDirectMessage(text=message, user_id=address, return_json=True)
            #print(result)

            # To utilize other Twitter APIs here see Twitters API documentation - https://developer.twitter.com/en/docs/basics/getting-started

        except Exception as e:
            logging.error(e)
            # see a list of exceptions returned from the api here - https://developer.twitter.com/en/docs/basics/response-codes
            logging.error("Error trying to send a Pinpoint Voice message")

        if i % len(pinpoint_long_codes):
            sleep(3)
        # Sleep 3 seconds between calls on the same long code avoid rate limiting

    logging.info("Complete")
    return "Complete"
