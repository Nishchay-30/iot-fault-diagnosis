import json
import ssl
import threading
import uuid
from collections import deque
from datetime import datetime

import certifi
import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="IoT Fault Diagnosis",
    page_icon="🏭",
    layout="wide"
)


# =========================================================
# HIVEMQ SETTINGS
# =========================================================

HIVEMQ_HOST = st.secrets["hivemq"]["host"]
HIVEMQ_PORT = int(st.secrets["hivemq"]["port"])
HIVEMQ_USERNAME = st.secrets["hivemq"]["username"]
HIVEMQ_PASSWORD = st.secrets["hivemq"]["password"]

SENSOR_TOPIC = "iot/factory/motor01/sensors"


# =========================================================
# DATA STORAGE
# =========================================================

class DataStore:

    def __init__(self):
        self.data = deque(maxlen=100)
        self.connected = False
        self.last_message = None
        self.lock = threading.Lock()

    def add_data(self, payload):

        sensors = payload.get("sensors", {})

        with self.lock:
            self.data.append({
                "time": datetime.now(),
                "temperature": float(
                    sensors.get("temperature_c", 0)
                ),
                "vibration": float(
                    sensors.get("vibration_mm_s", 0)
                ),
                "current": float(
                    sensors.get("current_a", 0)
                ),
                "pressure": float(
                    sensors.get("pressure_bar", 0)
                ),
                "rpm": float(
                    sensors.get("rpm", 0)
                ),
                "status": payload.get(
                    "machine_status",
                    "UNKNOWN"
                )
            })

            self.last_message = datetime.now()


# =========================================================
# MQTT CALLBACKS
# =========================================================

def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties
):

    if reason_code.is_failure:

        userdata.connected = False

        print(
            f"❌ HiveMQ connection failed: "
            f"{reason_code}"
        )

    else:

        userdata.connected = True

        print("✅ Connected to HiveMQ")

        client.subscribe(
            SENSOR_TOPIC,
            qos=1
        )

        print(
            f"Subscribed to: {SENSOR_TOPIC}"
        )


def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties
):

    userdata.connected = False

    print(
        f"Disconnected from HiveMQ: "
        f"{reason_code}"
    )


def on_message(
    client,
    userdata,
    message
):

    try:

        payload = json.loads(
            message.payload.decode("utf-8")
        )

        if message.topic == SENSOR_TOPIC:

            userdata.add_data(payload)

    except Exception as error:

        print(
            f"❌ MQTT data error: {error}"
        )


# =========================================================
# MQTT CONNECTION
# =========================================================

@st.cache_resource
def create_connection():

    store = DataStore()

    client_id = (
        "streamlit-"
        + uuid.uuid4().hex[:8]
    )

    client = mqtt.Client(
        callback_api_version=
            mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        protocol=mqtt.MQTTv311,
        userdata=store
    )

    client.username_pw_set(
        HIVEMQ_USERNAME,
        HIVEMQ_PASSWORD
    )

    # TLS / SSL
    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    client.tls_set_context(
        ssl_context
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.connect(
        HIVEMQ_HOST,
        HIVEMQ_PORT,
        keepalive=60
    )

    client.loop_start()

    return client, store


# =========================================================
# CONNECT
# =========================================================

try:

    mqtt_client, store = create_connection()

except Exception as error:

    st.error(
        f"❌ HiveMQ connection failed: {error}"
    )

    st.stop()


# =========================================================
# DIAGNOSIS
# =========================================================

def diagnose(row):

    temperature = row["temperature"]
    vibration = row["vibration"]
    current = row["current"]
    pressure = row["pressure"]
    rpm = row["rpm"]


    # Motor overload

    if (
        current >= 10
        and temperature >= 70
        and rpm < 1250
    ):

        return (
            "Motor Overload",
            "CRITICAL",
            95,
            "High current + high temperature "
            "+ reduced RPM",
            "Check motor load and mechanical resistance"
        )


    # Bearing fault

    if (
        vibration >= 7
        and temperature >= 70
    ):

        return (
            "Possible Bearing Fault",
            "HIGH",
            92,
            "High vibration + high temperature",
            "Inspect bearing, lubrication and alignment"
        )


    # Overheating

    if temperature >= 80:

        return (
            "Motor Overheating",
            "HIGH",
            94,
            "Temperature is above normal range",
            "Check cooling system and motor load"
        )


    # Low pressure

    if pressure < 1.2:

        return (
            "Low Pressure",
            "MEDIUM",
            94,
            "Pressure is below normal range",
            "Check pump, valves and leakage"
        )


    # High pressure

    if pressure > 4.0:

        return (
            "High Pressure",
            "HIGH",
            94,
            "Pressure is above normal range",
            "Check regulator and valves"
        )


    # Unbalance

    if vibration >= 6:

        return (
            "Possible Mechanical Unbalance",
            "HIGH",
            88,
            "Vibration is above normal range",
            "Inspect rotor balance and alignment"
        )


    # Normal

    return (
        "Normal Operation",
        "NONE",
        96,
        "All monitored values are within "
        "defined normal ranges",
        "Continue normal monitoring"
    )


# =========================================================
# HEADER
# =========================================================

st.title(
    "🏭 Knowledge-Driven IoT Fault Diagnosis Assistant"
)

st.caption(
    "Live MQTT monitoring via HiveMQ Cloud"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.success(
    "🟢 HiveMQ Dashboard Active"
)

st.sidebar.write(
    f"**Device:** motor01"
)

st.sidebar.write(
    f"**Topic:** {SENSOR_TOPIC}"
)


# =========================================================
# LIVE DASHBOARD
# =========================================================

@st.fragment(run_every=2)
def live_dashboard():

    with store.lock:

        rows = list(store.data)

        connected = store.connected

        last_message = store.last_message


    # -----------------------------------------------------
    # CONNECTION STATUS
    # -----------------------------------------------------

    if connected:

        st.success(
            "🟢 Connected to HiveMQ"
        )

    else:

        st.error(
            "🔴 Disconnected from HiveMQ"
        )


    # -----------------------------------------------------
    # WAITING FOR DATA
    # -----------------------------------------------------

    if not rows:

        st.warning(
            "Waiting for live sensor data..."
        )

        st.info(
            "Start synthetic_generator.py "
            "on your Mac."
        )

        return


    # -----------------------------------------------------
    # DATAFRAME
    # -----------------------------------------------------

    df = pd.DataFrame(rows)

    df["time"] = pd.to_datetime(
        df["time"]
    )

    df = df.set_index("time")

    latest = df.iloc[-1]


    # =====================================================
    # LIVE VALUES
    # =====================================================

    st.subheader(
        "📊 Live Sensor Values"
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "🌡 Temperature",
        f"{latest['temperature']:.2f} °C"
    )

    c2.metric(
        "〰 Vibration",
        f"{latest['vibration']:.2f} mm/s"
    )

    c3.metric(
        "⚡ Current",
        f"{latest['current']:.2f} A"
    )

    c4.metric(
        "💨 Pressure",
        f"{latest['pressure']:.2f} bar"
    )

    c5.metric(
        "⚙ RPM",
        f"{latest['rpm']:.0f}"
    )


    # =====================================================
    # DIAGNOSIS
    # =====================================================

    (
        fault,
        severity,
        confidence,
        reason,
        action
    ) = diagnose(latest)


    st.divider()

    st.subheader(
        "🧠 Knowledge-Based Diagnosis"
    )

    d1, d2, d3 = st.columns(3)

    d1.metric(
        "Diagnosis",
        fault
    )

    d2.metric(
        "Severity",
        severity
    )

    d3.metric(
        "Confidence",
        f"{confidence}%"
    )

    st.info(
        f"**Reason:** {reason}"
    )

    st.warning(
        f"**Recommended Action:** {action}"
    )


    # =====================================================
    # GRAPHS
    # =====================================================

    st.divider()

    st.subheader(
        "📈 Live Sensor Graphs"
    )

    col1, col2 = st.columns(2)


    with col1:

        st.write(
            "🌡️ Temperature"
        )

        st.line_chart(
            df[["temperature"]],
            height=300
        )


    with col2:

        st.write(
            "〰️ Vibration"
        )

        st.line_chart(
            df[["vibration"]],
            height=300
        )


    col3, col4 = st.columns(2)


    with col3:

        st.write(
            "⚡ Motor Current"
        )

        st.line_chart(
            df[["current"]],
            height=300
        )


    with col4:

        st.write(
            "💨 Pressure"
        )

        st.line_chart(
            df[["pressure"]],
            height=300
        )


    st.write(
        "⚙️ Motor RPM"
    )

    st.line_chart(
        df[["rpm"]],
        height=300
    )


    # =====================================================
    # LAST DATA
    # =====================================================

    if last_message:

        st.caption(
            "Last MQTT message received: "
            + last_message.strftime(
                "%H:%M:%S"
            )
        )


    # =====================================================
    # RAW DATA
    # =====================================================

    with st.expander(
        "🔍 View Raw Data"
    ):

        st.dataframe(
            df.tail(20),
            width="stretch"
        )


# =========================================================
# RUN
# =========================================================

live_dashboard()
