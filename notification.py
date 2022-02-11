from models import booksubjectsModel, userpntokenModel
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



def sendsmsmessage(access_key_id,access_key,number,message):
    sns = boto3.client("sns", 
                        aws_access_key_id=access_key_id,
                        aws_secret_access_key=access_key
                    )
    no = '+91'+str(number)
    sns.publish(
        PhoneNumber=no,
        Message= message 
    )