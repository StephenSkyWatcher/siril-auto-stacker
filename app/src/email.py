import smtplib
import imghdr
from email.message import EmailMessage

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


email_subject = "Stack complete"
stack_details = "\nAndromeda Galaxy: 3hr (60 frames)"
image_url = '/home/stephen/Pictures/andromeda_galaxy/lights/process/stacked_light_postprocessed_sm.jpg'

"""
"""
"""
"""


sms_receiver_email_address = "6032336275@vtext.com"
mms_receiver_email_address = "6032336275@vzwpix.com"

receiver_email_address = mms_receiver_email_address
# receiver_email_address = "6032336275@mypixmessages.com"

# sender_email_address = 'stephenyoung7267@gmail.com'
# email_smtp = "smtp.gmail.com"
# email_port = 587
# email_password = 'ugyb ptcx wuyc gfgv'

sender_email_address = 'stephen@theyoungs.cloud'
email_smtp = 'mail.privateemail.com'
email_port = 587
email_password = 'Dalekini21!'

# create an email message object
message = EmailMessage()
# configure email headers
message['Subject'] = email_subject
message['From'] = sender_email_address
message['To'] = receiver_email_address

# set email body text
message.set_content(stack_details)

with open(image_url, 'rb') as file:
    image_data = file.read()

message.add_attachment(image_data, maintype='image',
                       subtype=imghdr.what(None, image_data))


# set smtp server and port
server = smtplib.SMTP(email_smtp, email_port)
# identify this client to the SMTP server
server.ehlo()
# secure the SMTP connection
server.starttls()

# login to email account
server.login(sender_email_address, email_password)
# send email
server.send_message(message)
# close connection to server
server.quit()
