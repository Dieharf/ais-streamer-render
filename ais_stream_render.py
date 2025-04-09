
import asyncio
import websockets
import nest_asyncio
import json
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import io
import sys

nest_asyncio.apply()

# Redirect logs to a string buffer
log_stream = io.StringIO()
sys.stdout = sys.stderr = log_stream

API_KEY = 'e5aff806038e53f083d10f48595bf5be5072081a'

# --- EMAIL CONFIGURATION ---
TO_EMAIL = 'debashish1360@gmail.com'              # <- Replace with your receiving email
FROM_EMAIL = 'debashish1360@gmail.com'     # <- Replace with sender Gmail
APP_PASSWORD = 'uhcvosknwrjeuwkyrd'       # <- Replace with Gmail App Password

def email_csv(file_path, to_email, from_email, app_password, log_text=""):
    msg = EmailMessage()
    msg['Subject'] = 'AIS Data CSV and Logs from Render'
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content(f'Attached is the AIS CSV file from Render.\n\nLogs:\n{log_text}')

    with open(file_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_path)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(from_email, app_password)
        smtp.send_message(msg)

async def connect_ais_stream():
    url = f"wss://stream.aisstream.io/v0/stream?apikey={API_KEY}"
    data_records = []

    try:
        async with websockets.connect(url) as websocket:
            subscribe_message = {
                "APIKey": API_KEY,
                "BoundingBoxes": [[[1.3, 104], [1.22, 103.9]]],
                "Filtertime_utc": ["2025-04-04 07:30:00 +0000 UTC"]
            }
            await websocket.send(json.dumps(subscribe_message))

            print("Connection established. Listening to AIS data...")

            async for message_json in websocket:
                message = json.loads(message_json)
                if message.get("MessageType") == "PositionReport":
                    report = message["Message"]["PositionReport"]

                    data_to_write = {
                        'timestamp': message["MetaData"].get("time_utc", ""),
                        'mmsi': message["MetaData"].get("MMSI", ""),
                        'ShipName': report.get("ShipName", ""),
                        'latitude': report.get("Latitude", ""),
                        'longitude': report.get("Longitude", ""),
                        'speed': report.get("Sog", ""),
                        'course': report.get("Cog", "")
                    }

                    data_records.append(data_to_write)
                    print(pd.DataFrame([data_to_write]))

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving data...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        logs = log_stream.getvalue()

        if data_records:
            filename = f"ais_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df = pd.DataFrame(data_records)
            df.to_csv(filename, index=False)
            print(f"\n✅ Data saved to {filename}")
            print(df.head())

            email_csv(filename, TO_EMAIL, FROM_EMAIL, APP_PASSWORD, logs)
        else:
            # Still send logs even if no data was collected
            dummy_logfile = "ais_log_only.txt"
            with open(dummy_logfile, "w") as f:
                f.write(logs)
            email_csv(dummy_logfile, TO_EMAIL, FROM_EMAIL, APP_PASSWORD, logs)

if __name__ == "__main__":
    asyncio.run(connect_ais_stream())
