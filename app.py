import os
import random
import time
import smtplib
from datetime import datetime
from email.message import EmailMessage

import requests
from dotenv import load_dotenv

# Load credentials from the .env file
load_dotenv()

CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID")
WRITE_API_KEY = os.getenv("THINGSPEAK_WRITE_API_KEY")

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "").replace(" ", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

THINGSPEAK_URL = "https://api.thingspeak.com/update"

TEMPERATURE_LIMIT = 35.0
HUMIDITY_LIMIT = 80.0

UPLOAD_INTERVAL = 20  # Seconds
EMAIL_COOLDOWN = 600  # 10 minutes

last_email_time = 0


def generate_sensor_data():
    """Generate simulated temperature and humidity readings."""
    temperature = round(random.uniform(24.0, 40.0), 2)
    humidity = round(random.uniform(45.0, 90.0), 2)

    return temperature, humidity


def upload_to_thingspeak(temperature, humidity):
    """Upload sensor readings to ThingSpeak."""

    payload = {
        "api_key": WRITE_API_KEY,
        "field1": temperature,
        "field2": humidity,
    }

    try:
        response = requests.post(
            THINGSPEAK_URL,
            data=payload,
            timeout=15,
        )
        response.raise_for_status()

        entry_id = response.text.strip()

        if entry_id and entry_id != "0":
            print(f"Cloud upload successful. Entry ID: {entry_id}")
            return True

        print("Cloud upload was not accepted. Check your API key and channel.")
        return False

    except requests.RequestException as error:
        print(f"Cloud upload error: {error}")
        return False


def send_email_alert(temperature, humidity, alerts):
    """Send an email notification when sensor readings exceed limits."""

    global last_email_time

    if not EMAIL_SENDER or not EMAIL_APP_PASSWORD or not EMAIL_RECEIVER:
        print("Email alert skipped: Email settings are missing in .env.")
        return

    current_time = time.time()

    if current_time - last_email_time < EMAIL_COOLDOWN:
        print("Email alert skipped: 10-minute cooldown is active.")
        return

    message = EmailMessage()
    message["Subject"] = "IoT Cloud Monitoring - Sensor Alert"
    message["From"] = EMAIL_SENDER
    message["To"] = EMAIL_RECEIVER

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    alert_details = "\n".join(alerts)

    message.set_content(
        f"""
IoT CLOUD MONITORING SYSTEM
SENSOR ALERT

Time: {timestamp}

Temperature: {temperature} °C
Humidity: {humidity} %

Alert Details:
{alert_details}

Please check your environment and take necessary action.

This is an automatic notification from your IoT monitoring system.
"""
    )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.send_message(message)

        last_email_time = current_time
        print("SUCCESS: Email alert sent successfully.")

    except Exception as error:
        print(f"Email alert error: {error}")


def check_alerts(temperature, humidity):
    """Check sensor readings and send email alerts when necessary."""

    alerts = []

    if temperature > TEMPERATURE_LIMIT:
        alert = (
            f"High temperature: {temperature} °C "
            f"exceeds {TEMPERATURE_LIMIT} °C."
        )
        print("ALERT:", alert)
        alerts.append(alert)

    if humidity > HUMIDITY_LIMIT:
        alert = (
            f"High humidity: {humidity}% "
            f"exceeds {HUMIDITY_LIMIT}%."
        )
        print("ALERT:", alert)
        alerts.append(alert)

    if alerts:
        send_email_alert(temperature, humidity, alerts)
    else:
        print("Status: Normal. No alerts detected.")


def main():
    if not CHANNEL_ID or not WRITE_API_KEY:
        print("ERROR: ThingSpeak credentials are missing.")
        print("Check your .env file.")
        return

    print("======================================")
    print(" IoT Cloud Monitoring System")
    print("======================================")
    print(f"Channel ID: {CHANNEL_ID}")
    print("Email alerts: Enabled" if EMAIL_SENDER else "Email alerts: Not configured")
    print("Starting sensor simulation...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            temperature, humidity = generate_sensor_data()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\nTimestamp: {timestamp}")
            print(f"Temperature: {temperature} °C")
            print(f"Humidity: {humidity} %")

            check_alerts(temperature, humidity)

            upload_to_thingspeak(temperature, humidity)

            print(f"Next reading in {UPLOAD_INTERVAL} seconds.")
            time.sleep(UPLOAD_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")


if __name__ == "__main__":
    main()