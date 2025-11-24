##READ before starting out!
##this code should be run inside 'terminal'. the below sentence that starts with python3 needs to be adjusted and copy pasted inside terminal
##hit enter once pasted, code starts running
##use control + C to stop code from running (mac)
##Note: this file should be up and running on a device that is connected to the same wifi network as the wearables

## the sentence below is basically a pathway to this file, adjust it. the pathway is capslock sensitive!

## python3 /Users/patricianagtzaam/Desktop/HFDC_AL/HFDC_Wireless_3.py


# Import required modules
import serial
import time
import sqlite3
import threading
from pythonosc.udp_client import SimpleUDPClient
from pythonosc import dispatcher, osc_server
from collections import deque


##save temp in vals
##A
VAL1 = 0.0
VAL2 = 0.0
VAL3 = 0.0
##B
VAL4 = 0.0
VAL5 = 0.0
VAL6 = 0.0

##Scaling baselines values
##A
Baseline0_1 = 0.0
Baseline0_2 = 0.0
Baseline0_3 = 0.0
##B
Baseline0_4 = 0.0
Baseline0_5 = 0.0
Baseline0_6 = 0.0

##triggers from wearables
##A
VALA = 0.0
VALB = 0.0
VALC = 0.0
##B
VALD = 0.0
VALE = 0.0
VALF = 0.0

##triggers from python
VALTeamA = None
VALTeamB = None


#  Set up OSC Client (to send data to Resolume)
# open Resolume/wire to check IP adress per different location
##RESULOME_IP = '10.99.20.87' 
##RESULOME_PORT = 7000  
##client1 = SimpleUDPClient(RESULOME_IP, RESULOME_PORT)

##webapp frank
RESULOME_IP = '10.2.1.218' 
RESULOME_PORT = 7000  
client = SimpleUDPClient(RESULOME_IP, RESULOME_PORT)

#  Set up OSC Server (to receive data)

def print_osc_data(address, *args):
    global VAL1, VAL2, VAL3, VAL4, VAL5, VAL6, VALA, VALB, VALC, VALD, VALE, VALF, Baseline0_1, Baseline0_2, Baseline0_3, Baseline0_4, Baseline0_5, Baseline0_6, Baseline0_7

    print(f"Received OSC message on {address}: {args}")
    
    if len(args) > 0:
        try:
            float_values = [float(float(arg)) for arg in args]
        except ValueError:
            print("❌ Could not convert OSC args to int.")
            return

        # Save the data
        data_string = ', '.join(map(str, float_values))
        save_to_db(address, data_string)
        send_to_resolume(address, *float_values)

        # Save to data to vals
##  Arduino 1
        if address == "/arduino1/sensordata":
            VAL1 = float_values[0]
##            print(f"✅ VAL1 updated: {VAL1}")
        elif address == "/arduino1/Baseline0_1":
            Baseline0_1 = float_values[0]
##            print(f"✅ Baseline0-1 updated: {Baseline0_1}")
        elif address == "/trigger/wearableA":
            VALA = float_values[0]
##            print(f"✅ VALA updated: {VALA}")
            
##  Arduino 2           
        elif address == "/arduino2/sensordata":
            VAL2 = float_values[0]
##            print(f"✅ VAL2 updated: {VAL2}")
        elif address == "/arduino2/Baseline0_2":
            Baseline0_2 = float_values[0]
##            print(f"✅ Baseline0-2 updated: {Baseline0_2}")          
        elif address == "/trigger/wearableB":
            VALB = float_values[0]
##            print(f"✅ VALB updated: {VALB}")

##  Arduino 3
        elif address == "/arduino3/sensordata":
            VAL3 = float_values[0]
##            print(f"✅ VAL3 updated: {VAL3}")
        elif address == "/arduino3/Baseline0_3":
            Baseline0_3 = float_values[0]
##            print(f"✅ Baseline0-3 updated: {Baseline0_3}")
        elif address == "/trigger/wearableC":
            VALC = float_values[0]
##            print(f"✅ VALC updated: {VALC}")
##  Arduino 4
        elif address == "/arduino4/sensordata":
            VAL4 = float_values[0]
##            print(f"✅ VAL4 updated: {VAL4}")
        elif address == "/arduino4/Baseline0_4":
            Baseline0_4 = float_values[0]
##            print(f"✅ Baseline0-4 updated: {Baseline0_4}")
        elif address == "/trigger/wearableD":
            VALD = float_values[0]
##            print(f"✅ VALD updated: {VALD}")
##  Arduino 5
        elif address == "/arduino5/sensordata":
            VAL5 = float_values[0]
##            print(f"✅ VAL5 updated: {VAL5}")
        elif address == "/arduino5/Baseline0_5":
            Baseline0_5 = float_values[0]
##            print(f"✅ Baseline0-5 updated: {Baseline0_5}")
        elif address == "/trigger/wearableE":
            VALE = float_values[0]
##            print(f"✅ VALE updated: {VALE}")
##  Arduino 6
        elif address == "/arduino6/sensordata":
            VAL6 = float_values[0]
##            print(f"✅ VAL6 updated: {VAL6}")
        elif address == "/arduino6/Baseline0_6":
            Baseline0_6 = float_values[0]
##            print(f"✅ Baseline0-6 updated: {Baseline0_6}")
        elif address == "/trigger/wearableF":
            VALF = float_values[0]
##            print(f"✅ VALF updated: {VALF}")
            
            
        check_for_trigger_matches()
        calculate_and_send_team_averageA()
        calculate_and_send_team_averageB()
        check_team_matches()
        check_team_matchesAVG()
        
    else:
        print("Error: No values received")


def reset_all_vals():
    global VAL1, VAL2, VAL3, VAL4, VAL5, VAL6
    VAL1, VAL2, VAL3 = 0.0, 0.0, 0.0
    VAL4, VAL5, VAL6 = 0.0, 0.0, 0.0
       

### After setting VAL1 or VAL2:
##  Do we match them up specifically, so A from team 1 and A from team 2 are automatically matched?
## or just any match in  general? and how do i filter out which is which?

avgA1 = None
avgB1 = None
averageA = 0.0
averageB = 0.0


##calculate team avg raw data

# Store the last 10 average values for Team B
teamA_history = deque(maxlen=10)
avgA1 = 0.0  # latest 3-sensor average

def calculate_and_send_team_averageA():
    global avgA1

    # --- Step 1: Compute the average of 3 sensor values ---
    team_valsA = [VAL1, VAL2, VAL3]
    valid_valsA = [v for v in team_valsA if v != 0.0]

    if not valid_valsA:
        print("⚠️ No valid sensor values for Team A.")
        return

    avgA1 = float(sum(valid_valsA)) / len(valid_valsA)

    # --- Step 2: Add this to the rolling history (max 10 items) ---
    teamA_history.append(avgA1)

    # --- Step 3: Compute the average of the last 10 readings ---
    averageA = sum(teamA_history) / len(teamA_history)

    # --- Step 4: Output and send ---
    print(f"📊 Team A (3-sensor avg): {avgA1:.5f}")
    print(f"📈 Team A (10x rolling avg): {averageA:.5f}")

    client.send_message("/avg A", float(averageA))


# Store the last 10 average values for Team B
teamB_history = deque(maxlen=10)
avgB1 = 0.0  # latest 3-sensor average

def calculate_and_send_team_averageB():
    global avgB1

    # --- Step 1: Compute the average of 3 sensor values ---
    team_valsB = [VAL4, VAL5, VAL6]
    valid_valsB = [v for v in team_valsB if v != 0.0]

    if not valid_valsB:
        print("⚠️ No valid sensor values for Team B.")
        return

    avgB1 = float(sum(valid_valsB)) / len(valid_valsB)

    # --- Step 2: Add this to the rolling history (max 10 items) ---
    teamB_history.append(avgB1)

    # --- Step 3: Compute the average of the last 10 readings ---
    averageB = sum(teamB_history) / len(teamB_history)

    # --- Step 4: Output and send ---
    print(f"📊 Team B (3-sensor avg): {avgB1:.5f}")
    print(f"📈 Team B (10x rolling avg): {averageB:.5f}")

    client.send_message("/avg B", float(averageB))



def check_team_matchesAVG():
    global averageA, averageB
    MARGIN = 0.3

    if averageA != 0.0 and averageB != 0.0:
        if round(abs(averageA - averageB), 4) <= MARGIN:
            print(f"🎯 Match found: A={averageA:.2f}, B={averageB:.2f}")
            client.send_message("/trigger/matchTeamAVG", 1)
        else:
##            print(f"❌ No match: A={averageA:.2f}, B={averageB:.2f}")
            client.send_message("/trigger/matchTeamAVG", 0)
                        
sensor_pairs = [
    ("VAL1", "VAL4"),
    ("VAL2", "VAL5"),
    ("VAL3", "VAL6"),
]

def check_for_trigger_matches():
    MARGIN = 0.3
    for var1, var2 in sensor_pairs:
        val1 = globals().get(var1)
        val2 = globals().get(var2)

        if val1 != 0.0 and val2 != 0.0:
            if round(abs(val1 - val2), 4) <= MARGIN:
##                print(f"🎯 Match found: {var1}={val1}, {var2}={val2}")
                client.send_message(f"/trigger/match/{var1}_{var2}", 1)
            else:
                    client.send_message(f"/trigger/match/{var1}_{var2}", 0)
##                    print(f"NO match1")

team_a = ["VAL1", "VAL2", "VAL3"]
team_b = ["VAL4", "VAL5", "VAL6"]

def check_team_matches():
    MARGIN = 0.3

    for var_a in team_a:
        for var_b in team_b:
            val_a = globals().get(var_a)
            val_b = globals().get(var_b)

            if val_a is not None and val_b is not None:
                if round(abs(val_a - val_b), 4) <= MARGIN:
##                    print(f"🎯 Match between {var_a} (A) and {var_b} (B): {val_a} ≈ {val_b}")
                    client.send_message(f"/match/{var_a[-1]}{var_b[-1]}", 1)
                else:

                    
                        client.send_message(f"/match/{var_a[-1]}{var_b[-1]}", 0)
##                        print(f"NO match")


   
IP = "0.0.0.0"
PORT = 8000
dispatcher = dispatcher.Dispatcher()
## Add more dispatcher maps if we have more wearables

dispatcher.map("/arduino1/sensordata", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino2/sensordata", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino3/sensordata", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino4/sensordata", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino5/sensordata", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino6/sensordata", print_osc_data)  # Listen to all OSC messages


##dispatcher.map("/trigger/wearableA", print_osc_data)  # Listen to all OSC messages
##dispatcher.map("/trigger/wearableB", print_osc_data)  # Listen to all OSC messages
##dispatcher.map("/trigger/wearableC", print_osc_data)  # Listen to all OSC messages
##dispatcher.map("/trigger/wearableD", print_osc_data)  # Listen to all OSC messages
##dispatcher.map("/trigger/wearableE", print_osc_data)  # Listen to all OSC messages
##dispatcher.map("/trigger/wearableF", print_osc_data)  # Listen to all OSC messages

dispatcher.map("/arduino1/Baseline0_1", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino2/Baseline0_2", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino3/Baseline0_3", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino4/Baseline0_4", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino5/Baseline0_5", print_osc_data)  # Listen to all OSC messages
dispatcher.map("/arduino6/Baseline0_6", print_osc_data)  # Listen to all OSC messages

server = osc_server.ThreadingOSCUDPServer((IP, PORT), dispatcher)

# Run OSC Server in a separate thread so the script doesn't get stuck
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

print(f"Listening for OSC messages on {IP}:{PORT}...")

#  Configure SQLite Database / saves data locally on computer, change file name if needed or to reflect
## a certain day or test.
## NOTE: below there is again a  call to the same file, make sure to change name accordingly
conn = sqlite3.connect('/Users/patricianagtzaam/Desktop/HFDC_AL/data/ALtest0', check_same_thread=False)
cursor = conn.cursor()

# Create table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS SensorData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        source_address TEXT,
        data_values TEXT
    )
''')
conn.commit()

def save_to_db(address, data_string):
    try:
        # Create a fresh connection and cursor per function call
        conn = sqlite3.connect('/Users/patricianagtzaam/Desktop/HFDC_AL/data/ALtest0')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO SensorData (source_address, data_values) 
            VALUES (?, ?)
        ''', (address, data_string))
        
        conn.commit()
       

    except Exception as e:
        print(f"Error saving to DB: {e}")


##        client.send_message("/person1/sensor1", float(p1s1))
 #       client.send_message("/trigger/close_match", 1)
 
#  Function to Send Data to Resolume
def send_to_resolume(address, *values):
    try:
        for i, value in enumerate(values, start=1):
            client.send_message(f"{address}/sensor{i}", float(value))
##            client.send_message(f"/composition/layers/6/clips/1/dashboard/link1", float(VALTeamA))
            
##        print(f"Sent OSC from {address}: {values}")
    except Exception as e:
        print(f"Error sending OSC: {e}")
        
## send trigger statements to resolume
##  one is comparing all the data in python to see if the values match witheach other
##   the others are triggers received from the arduino's     
        
 #       client.send_message("/trigger/wearables", VALA)
 #       client.send_message("/trigger/wearables", VALB)
 #       client.send_message("/trigger/wearables", VALC)
  #      client.send_message("/trigger/wearables", VALD)
 #       client.send_message("/trigger/wearables", VALE)
 #       client.send_message("/trigger/wearables", VALF)
 #       client.send_message("/trigger/wearables", VAL100)


try:
    while True:
        reset_all_vals()   # set everything to 0
        time.sleep(1)      # OSC messages during this second will overwrite
except KeyboardInterrupt:
    print("Exiting...")
    conn.close()
