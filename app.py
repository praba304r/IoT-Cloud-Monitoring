import random
import time
from datetime import datetime

def read_sensor():
    """Simulate temperature and humidity sensor readings."""
    temperature = round(random.uniform(25.0, 40.0), 2)
    humidity = round(random.uniform(40.0, 90.0), 2)

    return temperature, humidity


def check_alerts(temperature, humidity):
    """Check sensor readings against the configured limits."""

    if temperature > 35:
        print("ALERT: High temperature detected!")

    if humidity > 80:
        print("ALERT: High humidity detected!")


def main():
    print("Real-Time IoT Data Monitoring System")
    print("=" * 40)

    try:
        while True:
            temperature, humidity = read_sensor()

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            print(f"\nTime: {timestamp}")
            print(f"Temperature: {temperature} °C")
            print(f"Humidity: {humidity} %")

            check_alerts(temperature, humidity)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    main()