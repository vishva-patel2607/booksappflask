import boto3
import os


def sendverifymail(sender,recepient,template):
    try:
        ses_client = boto3.client('ses',
                                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                                )
        ses_client.send_email(
            Source=sender,
            Destination={'ToAddresses': [recepient]},
            Message={
                'Subject': {'Data': 'Please verify your account'},
                'Body': {
                    'Html': {'Data': template}
                }
            }
        )
        print("mail sent to "+recepient)
    except:
        raise("Failed to send the mail") 
        

def sendchangepasswordmail(sender,recepient,template):
        try:
            ses_client = boto3.client('ses',
                                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                                )
            ses_client.send_email(
                Source=sender,
                Destination={'ToAddresses': [recepient]},
                Message={
                    'Subject': {'Data': 'Change password of your account'},
                    'Body': {
                        'Html': {'Data': template}
                    }
                }
            )
            print("mail sent to "+recepient)
        except:
            raise("Failed to send the mail")      

    
'''
class Mailer:

    def __init__(self,app):
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 465
        app.config['MAIL_USE_SSL'] = True
        app.config['MAIL_USERNAME'] = "booksapp2021@gmail.com"
        app.config['MAIL_PASSWORD'] = "Abc@18bce260"
        self.mail = Mail(app)
        self.sender = app.config['MAIL_USERNAME']

    def sendverifymail(self,recepient,template,url):
        #try:
        msg = Message(
            subject='Verify your account and email address', 
            recipients=[recepient], 
            html=render_template(template,url = url), 
            sender=self.sender, 
            )
        self.mail.send(msg)
        print('Mail sent')
        #except:
        #    print('Could not send the mail')

    def sendchangepasswordmail(self,recepient,template,url):
        try:
            msg = Message(
                subject='Change password of your account', 
                recipients=[recepient], 
                html=render_template(template,url = url), 
                sender=self.sender, 
                )
            self.mail.send(msg)
            print('mail sent')
        except:
            pass


'''



        

     
