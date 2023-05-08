import time
import board
import adafruit_dht
import pyrebase
import random
import RPi.GPIO as GPIO
import smbus

# Define configuration objects for configuring Firebase projects
config = {
  "apiKey": "AIzaSyDnIlW-N_dwCg6-eDpjFoVKRZ-z9AKnSiM",
  "authDomain": "girls-in-ict-2b1ea.firebaseapp.com",
  "databaseURL": "https://girls-in-ict-2b1ea-default-rtdb.firebaseio.com/",
  "storageBucket": "girls-in-ict-2b1ea.appspot.com"
}

# Initialize the Firebase application, create an instance for the Realtime Database, and save it to the db variable
firebase = pyrebase.initialize_app(config)

db = firebase.database()

# Set up GPIO for the buzzer, LED
# In the demo, the Led sensor means sprinkler and the buzzer means ultra-low frequency device
GPIO.setmode(GPIO.BCM)
buzzer_pin = 27
LED = 7
GPIO.setup(buzzer_pin, GPIO.OUT)
GPIO.setup(LED, GPIO.OUT)
GPIO.setmode(GPIO.BCM)
# Control of connected devices using I2C communication
bus = smbus.SMBus(1)
AINO = 0x40

# Operation to control DHT11 temperature and humidity sensor, set GPIO pin number to 26
dhtDevice = adafruit_dht.DHT11(board.D26)

# Defines the scale and melody of the buzzer
scale = [ 261, 294, 329, 349, 392, 440, 493, 523 ]
melody = [4, 4, 5, 5, 4, 4, 2, 4, 4, 2, 2, 1]

# Initializes an empty list for storing measured temperature values
temperature_list = []

# Function for reading gas concentration values from the gas sensor
def read_gas_sensor():
    bus.write_byte(0x48, AINO)
    gas_value = bus.read_byte(0x48)
    return gas_value

# Define function to save warning message to Firebase
# Temperature rise warning message
def save_tem_warning_to_firebase():
    data = {
        "message": "Warning! Temperature rises sharply.",
        "timestamp": currentTimeStr
    }
    db.child("warning").set(data)
    print("Warning message saved to Firebase.")
# Low humidity warning message
def save_hum_warning_to_firebase():
    data = {
        "message": "Warning! Humidity is too low.",
        "timestamp": currentTimeStr
    }
    db.child("warning").set(data)
    print("Warning message saved to Firebase.")
# Gas numerical value warning message
def save_gas_warning_to_firebase():
    data = {
        "message": "Warning! Gas is detected.",
        "timestamp": currentTimeStr
    }
    db.child("warning").set(data)
    print("Warning message saved to Firebase.")

# Function that converts timestamps into date and time formats    
def timestamp_to_date(timestamp):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))           

while True:
    try:
        # Read temperature, humidity and gas values from sensor
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        gas_value = read_gas_sensor()
        
        # Recall timestamp value as human readable date and time string
        currentTime = int(time.time())
        currentTimeStr = timestamp_to_date(currentTime)
        
        data = {
            "Temperature": temperature_c,
            "Humidity": humidity,
            "Gas": gas_value,
            "timestamp": currentTimeStr
        }
        
        # Check data values to store in Firebase
        print("Data: ", data)
        
        # Code for storing data in the Firebase Realtime Database
        # Update the current measured temperature, humidity, gas concentration, and timestamp values to the "Now" path in real time
        db.child("Now").update(data)
        # Stores all previously measured data (temperature, humidity, gas concentration, timestamp) in a list format in the "history" path
        db.child("history").push(data)
        
        
        print("Sent to Firebase")
        
        
        # Add current temperature to list
        temperature_list.append(temperature_c)
        
        # Operation of the LED sensor (meaning sprinkler) when humidity is less than 45
        if humidity <= 45:
            # Send humidity warning messages to Firebase
            save_hum_warning_to_firebase()
            
            print("warning - Humidity")
            
            GPIO.output(LED, GPIO.HIGH)
            time.sleep(0.5)
                
            GPIO.output(LED, GPIO.LOW)
        
        GPIO.output(LED, GPIO.LOW)
        
        # When the gas value exceeds 170, operate the led sensor and buzzer
        # Limit line of gas value changes depending on sensor installation area
        if gas_value > 170:
            save_gas_warning_to_firebase()
            p = GPIO.PWM(buzzer_pin, 100)
            p.start(100)
            p.ChangeDutyCycle(90)
            print("warning - Gas")
            GPIO.output(LED, GPIO.HIGH)
            time.sleep(0.5)
                
            for note in melody:
                p.ChangeFrequency(scale[note])
                if note == 6:
                    time.sleep(1)
                else:
                    time.sleep(0.5)
            
            p.stop()
            GPIO.output(LED, GPIO.LOW)
            
        GPIO.output(LED, GPIO.LOW)
          
        
        # Check if current temperature is 2 degrees higher than the first temperature in the list
        if len(temperature_list) >= 2 and temperature_c >= temperature_list[1] + 2:
            save_tem_warning_to_firebase()
           
            p = GPIO.PWM(buzzer_pin, 100)
            p.start(100)
            p.ChangeDutyCycle(90)
            
            GPIO.output(LED, GPIO.HIGH)

            print("warning - Temperature")
            time.sleep(0.5)

            for note in melody:
                p.ChangeFrequency(scale[note])
                if note == 6:
                    time.sleep(1)
                else:
                    time.sleep(0.5)

            p.stop()
            GPIO.output(LED, GPIO.LOW)
        
            # Reset temperature list after warning message
            temperature_list = []

        # If the length of the list whose temperature is constantly being measured is greater than 30, remove the oldest value
        if len(temperature_list) >= 30:
            temperature_list.pop(0)

    # Code for handling errors that may occur while reading temperature and humidity values from the DHT11 sensor
    except RuntimeError as error:
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error
    
    # Wait 5 seconds before the next code executes
    # Can avoid problems by waiting for the system to stabilize for 5 seconds
    time.sleep(5.0)





