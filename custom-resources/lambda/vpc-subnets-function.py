from botocore.vendored import requests

import boto3
import json
import logging
import os
import sys

# set up critical path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# set up logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# required by CFN response to uniquely identify the custom resource
physical_resource_id = 'Lambda-%s-CgsPCAIPAwo' % __file__[:-3]

def lambda_handler(event, context):
    if 'VpcId' not in event:
        raise Exception('Event is missing VpcId')

    vpcId = event['VpcId']

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

    # check if CFN made the request, return response to the specified location
    if 'ResponseUrl' in event:
        responseUrl = event['ResponseUrl']

        # the following properties are required in a CFN response
        responseBody = {}
        responseBody['Status'] = status
        responseBody['Reason'] = context.log_stream_name
        responseBody['PhysicalResourceId'] = physical_resource_id
        responseBody['StackId'] = event['StackId']
        responseBody['RequestId'] = event['RequestId']
        responseBody['LogicalResourceId'] = event['LogicalResourceId']
        responseBody['Data'] = subnets

        jsonResponseBody = json.dumps(responseBody)
        logger.info("Response Body: %s", jsonResponseBody)

        headers = {
            'content-type' : '',
            'content-length' : str(length(jsonResponseBody)),
        }

        try:
            response = requests.put(responseUrl, data=jsonResponseBody, headers=headers)
            logger.info("CFN response code: %s", response)
        except Exception, e:
            logger.info("CFN request failed with exception: %s", e)

    return subnets;
