from botocore.vendored import requests

import boto3
import json
import logging

# set up logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Event: %s,  Context %s", event, context)

    if 'ResourceProperties' not in event or 'VpcId' not in event['ResourceProperties'] :
        raise Exception('Event is missing ResourceProperties.VpcId')

    vpcId = event['ResourceProperties']['VpcId']

    logger.info("Retrieving subnets for VPC %s", vpcId)

    ec2_client = boto3.client('ec2')
    subnets = ec2_client.describe_subnets(
        Filters = [
            {
                'Name':'vpc-id',
                'Values':[
                    vpcId
                ]
            }
        ]
    )

    logger.info("VPC %s contains subnets: %s", vpcId, subnets)

    # create a more palatable comma separated format to be consumed
    subnetIds = ",".join([subnet['SubnetId'] for subnet in subnets['Subnets']])

    # check if CFN made the request, return response to the specified location
    if 'ResponseURL' in event:

        responseUrl = event['ResponseURL']
        logger.info("Responding to CFN request on [%s]", responseUrl)

        # the following properties are required in a CFN response
        responseBody = {}
        responseBody['Status'] = 'SUCCESS'
        responseBody['Reason'] = context.log_stream_name
        responseBody['PhysicalResourceId'] = context.log_stream_name
        responseBody['StackId'] = event['StackId']
        responseBody['RequestId'] = event['RequestId']
        responseBody['LogicalResourceId'] = event['LogicalResourceId']
        responseBody['Data'] = {'Subnets':  subnetIds}

        jsonResponseBody = json.dumps(responseBody)
        logger.info("Response Body: %s", jsonResponseBody)

        headers = {
            'content-type' : '',
            'content-length' : str(len(jsonResponseBody)),
        }

        try:
            response = requests.put(responseUrl, data=jsonResponseBody, headers=headers)
            logger.info("CFN response code: %s", response)
        except Exception, e:
            logger.error("CFN request failed with exception: %s", e)

    return subnetIds;
