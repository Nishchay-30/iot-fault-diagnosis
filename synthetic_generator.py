import json
import random
import ssl
import time
import uuid
from datetime import datetime, timezone

import certifi
import paho.mqtt.client as mqtt


# =========================================================
# HIVEMQ CLOUD
# =========================================================

HIVEMQ_HOST = "1285e2f1b7e14c249b55489e3f2de0e3.s1.eu.hivemq.cloud"
HIVEMQ_PORT = 8883

# ENTER YOUR HIVEMQ MQTT CREDENTIALS HERE
HIVEMQ_USERNAME = "nishchayarora30"
HIVEMQ_PASSWORD = "domingo@123#"


# =========================================================
# MQTT TOPICS
# =========================================================

SENSOR_TOPIC = "iot/factory/motor01/sensors"
GROUND_TRUTH_TOPIC = "iot/factory/motor01/ground_truth"


# =========================================================
# MACHINE
# =========================================================

DEVICE_ID = "motor01"
LOCATION = "factory_line_01"
PUBLISH_INTERVAL = 2


# =========================================================
# FAULTS
# =========================================================

FAULTS = [
    "NORMAL",
    "NORMAL",
    "NORMAL",
    "NORMAL",
    "OVERHEATING",
    "BEARING_FAULT",
    "OVERLOAD",
    "LOW_PRESSURE",
    "HIGH_PRESSURE",
    "UNBALANCE"
]


# =========================================================
# MQTT CALLBACKS
# =========================================================

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"❌ Connection failed: {reason_code}")
    else:
        print("✅ Connected to HiveMQ Cloud")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"Disconnected from HiveMQ: {reason_code}")


# =========================================================
# NORMAL DATA
# =========================================================

def generate_normal_data():

    return {
        "temperature": round(max(20, random.gauss(55, 3)), 2),
        "vibration": round(max(0, random.gauss(2.0, 0.3)), 2),
        "current": round(max(0, random.gauss(6.0, 0.5)), 2),
        "pressure": round(max(0, random.gauss(2.5, 0.1)), 2),
        "rpm": round(max(0, random.gauss(1450, 30)), 2)
    }


# =========================================================
# FAULT DATA
# =========================================================

def generate_fault_data(fault):

    data = generate_normal_data()

    if fault == "OVERHEATING":
        data["temperature"] = round(random.uniform(80, 95), 2)
        data["current"] = round(random.uniform(8, 10), 2)

    elif fault == "BEARING_FAULT":
        data["vibration"] = round(random.uniform(7, 12), 2)
        data["temperature"] = round(random.uniform(70, 85), 2)

    elif fault == "OVERLOAD":
        data["current"] = round(random.uniform(10, 15), 2)
        data["temperature"] = round(random.uniform(70, 90), 2)
        data["rpm"] = round(random.uniform(900, 1250), 2)

    elif fault == "LOW_PRESSURE":
        data["pressure"] = round(random.uniform(0.5, 1.2), 2)

    elif fault == "HIGH_PRESSURE":
        data["pressure"] = round(random.uniform(4.0, 5.5), 2)

    elif fault == "UNBALANCE":
        data["vibration"] = round(random.uniform(6, 10), 2)
        data["rpm"] = round(random.uniform(1300, 1600), 2)

    return data


# =========================================================
# SEVERITY
# =========================================================

def get_severity(fault):

    return {
        "NORMAL": "NONE",
        "LOW_PRESSURE": "MEDIUM",
        "HIGH_PRESSURE": "HIGH",
        "OVERHEATING": "HIGH",
        "BEARING_FAULT": "HIGH",
        "OVERLOAD": "CRITICAL",
        "UNBALANCE": "HIGH"
    }.get(fault, "UNKNOWN")


# =========================================================
# MAIN
# =========================================================

def main():

    if HIVEMQ_USERNAME == "YOUR_USERNAME":
        print("❌ Please enter your HiveMQ username.")
        return

    if HIVEMQ_PASSWORD == "YOUR_NEW_PASSWORD":
        print("❌ Please enter your HiveMQ password.")
        return

    client_id = f"{DEVICE_ID}-{uuid.uuid4().hex[:8]}"

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311
    )

    client.username_pw_set(
        HIVEMQ_USERNAME,
        HIVEMQ_PASSWORD
    )

    # macOS SSL certificate fix
    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    client.tls_set_context(ssl_context)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    print("=" * 55)
    print("   KNOWLEDGE-DRIVEN IoT FAULT GENERATOR")
    print("=" * 55)
    print(f"Device : {DEVICE_ID}")
    print(f"Broker : {HIVEMQ_HOST}")
    print("-" * 55)

    try:
        print("Connecting to HiveMQ Cloud...")

        client.connect(
            HIVEMQ_HOST,
            HIVEMQ_PORT,
            keepalive=60
        )

        client.loop_start()

        time.sleep(1)

    except Exception as error:
        print("❌ HiveMQ connection error:")
        print(error)
        return

    print()
    print("🚀 Synthetic data generation started")
    print("Press Ctrl+C to stop")
    print()

    try:

        while True:

            fault = random.choice(FAULTS)

            values = generate_fault_data(fault)

            timestamp = datetime.now(
                timezone.utc
            ).isoformat()

            sensor_data = {
                "device_id": DEVICE_ID,
                "location": LOCATION,
                "timestamp": timestamp,
                "machine_status":
                    "RUNNING" if fault == "NORMAL" else "FAULT",
                "sensors": {
                    "temperature_c": values["temperature"],
                    "vibration_mm_s": values["vibration"],
                    "current_a": values["current"],
                    "pressure_bar": values["pressure"],
                    "rpm": values["rpm"]
                }
            }

            ground_truth = {
                "device_id": DEVICE_ID,
                "timestamp": timestamp,
                "actual_fault": fault,
                "severity": get_severity(fault)
            }

            sensor_json = json.dumps(sensor_data)
            ground_truth_json = json.dumps(ground_truth)

            sensor_result = client.publish(
                SENSOR_TOPIC,
                sensor_json,
                qos=1
            )

            truth_result = client.publish(
                GROUND_TRUTH_TOPIC,
                ground_truth_json,
                qos=1
            )

            print("📡 SENSOR DATA")
            print(
                f"Temperature : {values['temperature']} °C"
            )
            print(
                f"Vibration   : {values['vibration']} mm/s"
            )
            print(
                f"Current     : {values['current']} A"
            )
            print(
                f"Pressure    : {values['pressure']} bar"
            )
            print(
                f"RPM         : {values['rpm']}"
            )

            print(f"🔧 Fault     : {fault}")
            print(f"⚠️ Severity  : {get_severity(fault)}")

            if sensor_result.rc != mqtt.MQTT_ERR_SUCCESS:
                print("❌ Sensor publish failed")

            if truth_result.rc != mqtt.MQTT_ERR_SUCCESS:
                print("❌ Ground truth publish failed")

            print("-" * 55)

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:

        print()
        print("🛑 Generator stopped.")

    finally:

        client.loop_stop()
        client.disconnect()

        print("✅ Disconnected from HiveMQ.")


if __name__ == "__main__":
    main()
