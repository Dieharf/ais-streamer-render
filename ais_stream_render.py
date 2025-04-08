# -*- coding: utf-8 -*-
"""ais_stream_render.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/18uZmc5IH5bv6OoeIXveI3wOwxJacCe37
"""

pip -q install websockets asyncio nest_asyncio

import asyncio
import websockets
import nest_asyncio
import json
import csv

import asyncio
import websockets
import json
import pandas as pd
import csv
from datetime import datetime

API_KEY = 'e5aff806038e53f083d10f48595bf5be5072081a'

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

            print("Connection established. Listening to AIS data... Press Ctrl+C to stop.")

            async for message_json in websocket:
                message = json.loads(message_json)
                if message.get("MessageType") == "PositionReport":
                    report = message["Message"]["PositionReport"]

                    data_to_write = {
                        'timestamp': message["MetaData"].get("time_utc", ""),
                        'mmsi': message["MetaData"].get("MMSI", ""),
                        'ShipName': report.get("ShipName",""),
                        'latitude': report.get("Latitude", ""),
                        'longitude': report.get("Longitude", ""),
                        'speed': report.get("Sog", ""),
                        'course': report.get("Cog", "")

                    }

                    data_records.append(data_to_write)

                    # Optional: print row as confirmation
                    print(pd.DataFrame([data_to_write]))

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving data...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Save to CSV
        if data_records:
            filename = f"ais_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df = pd.DataFrame(data_records)
            df.to_csv(filename, index=False)
            print(f"\n✅ Data saved to {filename}")
            print(df.head())  # Show preview
        else:
            print("No data collected.")

if __name__ == "__main__":
    import nest_asyncio # Import nest_asyncio
    nest_asyncio.apply() # Apply nest_asyncio patch
    asyncio.run(connect_ais_stream()) # Run the asynchronous function
