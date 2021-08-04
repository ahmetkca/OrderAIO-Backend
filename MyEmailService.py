import time
from config import SMTP_HOST, SMTP_USER, SMTP_PASS
from email.message import EmailMessage
from smtplib import SMTP_SSL, SMTP_SSL_PORT
import asyncio

async def send_verification_email(verification_code, email, register_email_url):
    await asyncio.sleep(0)
    # construct email
    email_message = EmailMessage()
    email_message['Subject'] = '[OrderAIO] Verify and Register'
    email_message['From'] = SMTP_USER
    email_message['To'] = email
    email_message.set_content(f'''
<span style="opacity: 0"> {time.time()} </span>
<div>Verification code: <b>{verification_code}</b></div>
<p>The Verification code will expire in 30 minutes.</p>
<p>Click below link to verify and register.</p>
<a href="{register_email_url}" target="_blank">Verify and Register</a>
<span style="opacity: 0"> {time.time()} </span>
''', subtype='html')

    # Connect, authenticate, and send mail
    smtp_server = SMTP_SSL(SMTP_HOST, port=SMTP_SSL_PORT)
    # smtp_server.set_debuglevel(1)  # Show SMTP server interactions
    smtp_server.login(SMTP_USER, SMTP_PASS)
    smtp_server.sendmail(SMTP_USER, email, email_message.as_bytes())

    # Disconnect
    smtp_server.quit()


# from fastapi_mail import FastMail, MessageSchema,ConnectionConfig

# conf = ConnectionConfig(
#     MAIL_USERNAME = SMTP_USER,
#     MAIL_PASSWORD = SMTP_PASS,
#     MAIL_FROM = SMTP_USER,
#     MAIL_PORT = 587,
#     MAIL_SERVER = SMTP_HOST,
#     MAIL_FROM_NAME = 'OrderAIO',
#     MAIL_TLS = True,
#     MAIL_SSL = False,
#     TEMPLATE_FOLDER = 'templates',
#     USE_CREDENTIALS = True,
# )


# async def send_verification_email(verification_code, email, register_email_url):
#     body={
# 		'verification_code': verification_code,
# 		'register_email_url': register_email_url}

#     message = MessageSchema(
#         subject="[OrderAIO] - Register - Verification Code",
#         recipients=[email],
#         template_body=body,
#         subtype='html',
#     )
#     fm = FastMail(conf)
#     res = await fm.send_message(message, template_name='verification_email.html')
#     print(res)

