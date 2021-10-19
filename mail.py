
from flask.templating import render_template
from flask_mail import Mail,Message



    

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
        msg = Message(
            subject='Verify your account and email address', 
            recipients=recepient, 
            html=render_template(template,url = url), 
            sender=self.sender, 
            )

    def sendchangepasswordmail(self,recepient,template,url):
        msg = Message(
            subject='Change password of your account', 
            recipients=recepient, 
            html=render_template(template,url = url), 
            sender=self.sender, 
            )
        

     
