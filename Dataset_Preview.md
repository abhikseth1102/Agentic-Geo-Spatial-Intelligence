# Dataset Preview (NOAA MarineCadastre)

If you need to quickly show your professor what the raw dataset looks like without launching Excel, you can use this preview.

## Data Dictionary
The raw dataset contains dozens of columns, but our ML pipeline isolates the following critical telemetry features:

| Column Name | Description | Example |
| :--- | :--- | :--- |
| **MMSI** | Unique maritime identification number for the vessel. | `368255870` |
| **BaseDateTime** | Timestamp of the ping (UTC). | `2023-08-28T00:00:00` |
| **LAT / LON** | GPS Coordinates (Latitude and Longitude). | `26.77494, -80.04933` |
| **SOG** | Speed Over Ground (Knots). | `12.6` |
| **COG** | Course Over Ground (Degrees bearing). | `139.9` |
| **VesselType** | Numerical code representing ship class (e.g., Cargo, Tanker). | `37.0` |

## Raw Dataset Sample (First 5 Rows)
This is exactly how the data looks coming directly from the U.S. Government servers before our AI processes it:

| MMSI | BaseDateTime | LAT | LON | SOG | COG | VesselType |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 368255870 | 2023-08-28T00:00:00 | 26.77494 | -80.04933 | 0.0 | 106.6 | 37.0 |
| 367556020 | 2023-08-28T00:00:01 | 30.76055 | -88.04936 | 0.0 | 298.1 | 31.0 |
| 367308990 | 2023-08-28T00:00:01 | 30.70455 | -88.03775 | 5.6 | 352.0 | 31.0 |
| 367088290 | 2023-08-28T00:00:03 | 30.32280 | -88.54891 | 12.6 | 139.9 | 30.0 |
| 368214170 | 2023-08-28T00:00:05 | 30.30045 | -88.51289 | 6.0 | 0.9 | 57.0 |

> [!TIP]
> **Data Scale:** The raw file (`AIS_2023_08_28.csv`) contains roughly **10 million** of these rows, mapping every ship in the U.S. on the day Hurricane Idalia formed.
