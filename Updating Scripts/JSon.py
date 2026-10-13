import json

def parse_sensor_string(line):
    """
    Parse a JSON line from serial and return a flat dictionary.
    Supports:
    - Seeed format (with EC, PH, CO2_DATA, Light)
    - Uno format (PH + CO2_DATA)
    """

    try:
        parsed = json.loads(line)

        # Flatten nested CO2_DATA
        if "CO2_DATA" in parsed and isinstance(parsed["CO2_DATA"], dict):
            parsed.update(parsed["CO2_DATA"])
            del parsed["CO2_DATA"]

        return parsed

    except Exception:
        # If it's not valid JSON, return empty dict
        return {}


def prepare_for_sheets(sensor_data, device_type, column_order):
    prefix = "SEEED_" if device_type == "seeed" else "UNO_"
    
    field_map = {
        f"{prefix}PH": sensor_data.get("PH"),
        f"{prefix}EC": sensor_data.get("EC"),
        f"{prefix}CO2": sensor_data.get("CO2"),
        f"{prefix}AirTemperature": sensor_data.get("AirTemperature"),
        f"{prefix}Humidity": sensor_data.get("Humidity"),
        f"{prefix}Light": sensor_data.get("Light"),
    }

    # modified to add in more columns when necessary and if the added columns don't match with the prefixes
    row = [ 
        field_map.get(col) if field_map.get(col) not in [None, ""]
        else sensor_data.get(col, "N/A")
        for col in column_order
        ]
    return row