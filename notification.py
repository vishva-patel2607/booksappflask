from models import userpntokenModel
import time
import boto3

def subscribetonotification(access_key_id,access_key,platformarn,usernumber,devicepushtoken,platform):
    sns = boto3.client("sns", 
                        aws_access_key_id=access_key_id,
                        aws_secret_access_key=access_key
                    )

    response = sns.create_platform_endpoint(
        PlatformApplicationArn=platformarn,
        Token=devicepushtoken,
    )

    awsarnendpoint = response['EndpointArn']

    token = userpntokenModel(
                    usernumber = usernumber,
                    devicetoken = devicepushtoken,
                    awsarnendpoint = awsarnendpoint,
                    platform = platform
                )
    token.insert()
    print("Subscribing usernumber:"+usernumber)



def getawsarnendpoint(usernumber,devicetoken):
    print("in the function")
    
    time.sleep(10)
    awsarnendpoint = str(usernumber+devicetoken)
    temp = userpntokenModel(
                    usernumber = usernumber,
                    devicetoken = devicetoken,
                    awsarnendpoint = awsarnendpoint
                )
    temp.insert()
    print(temp.details())