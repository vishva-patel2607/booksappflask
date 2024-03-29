import os
import boto3

def upload_file(access_key_id,access_key,file_name, bucket, body):
    object_name = 'book-image-folder/'+file_name
    s3_client = boto3.resource('s3',
                                aws_access_key_id=access_key_id,
                                aws_secret_access_key=access_key
                            )
    response = s3_client.Bucket(bucket).put_object(Key = object_name, Body = body,ACL = 'public-read')
    return response


def remove_file(access_key_id,access_key,file_name, bucket):
    object_name = 'book-image-folder/'+file_name
    s3_client = boto3.resource('s3',
                                aws_access_key_id=access_key_id,
                                aws_secret_access_key=access_key
                            )
    response = s3_client.Bucket(bucket).delete_objects(Delete={
                                                                    'Objects': [
                                                                        {
                                                                            'Key': object_name
                                                                        },
                                                                    ],
                                                                    'Quiet': True
                                                                })
    return response
    


def upload_invoice(access_key_id,access_key, bucket,file_name, body):
    object_name = 'booksapp-store-invoices/'+file_name
    s3_client = boto3.resource('s3',
                                aws_access_key_id=access_key_id,
                                aws_secret_access_key=access_key
                            )
    response = s3_client.Bucket(bucket).put_object(Key = object_name, Body = body,ACL = 'public-read',ContentType = "application/pdf")
    return response