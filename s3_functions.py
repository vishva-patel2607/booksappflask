import boto3

def upload_file(file_name, bucket, body):
    object_name = file_name
    s3_client = boto3.resource('s3')
    response = s3_client.Bucket(bucket).put_object(Key = file_name, Body = body)
    return response