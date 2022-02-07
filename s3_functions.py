import os
import boto3

def upload_file(file_name, bucket, body):
    object_name = 'book-image-folder/'+file_name
    s3_client = boto3.resource('s3',
                                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                            )
    response = s3_client.Bucket(bucket).put_object(Key = object_name, Body = body,ACL = 'public-read')
    return response