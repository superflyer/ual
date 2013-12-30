# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

# Create a text/plain message
msg = MIMEText('This is a test message.')

me = 'dfreeman@cs.stanford.edu'
# you == the recipient's email address
msg['Subject'] = 'Test'
msg['From'] = me
msg['To'] = me

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP('localhost')
s.sendmail(me, [me], msg.as_string())
s.quit()