import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

if not EMAIL_SENDER or not EMAIL_APP_PASSWORD or not EMAIL_RECEIVER:
    print("ERROR: Email settings are missing in the .env file.")
else:
    message = EmailMessage()
    message["Subject"] = "IoT Cloud Monitoring - Test Alert"
    message["From"] = EMAIL_SENDER
    message["To"] = EMAIL_RECEIVER
    message.set_content(
        "Congratulations! Your IoT Cloud Monitoring email alert system is working."
    )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.send_message(message)

        print("SUCCESS: Test email sent.")

    except Exception as error:
        print("ERROR:", error)