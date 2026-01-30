# 🗺️ UTM → GPX Converter

A Streamlit web application designed to convert UTM (Universal Transverse Mercator) coordinates into GPX files for GPS devices and mapping software.

## 📋 Features

* ✅ **File Upload**: Supports Excel (.xlsx) and CSV formats.
* ✅ **Coordinate Transformation**: Precise UTM → WGS84 (Lat/Lon) conversion.
* ✅ **Zone Selection**: Custom selection of UTM zones (32N, 33N, 34N, etc.).
* ✅ **Data Preview**: Interactive table view of your data.
* ✅ **Interactive Map**: Visual validation of points before export.
* ✅ **GPX Export**: Instant download of the generated GPX file.
* ✅ **Error Handling**: Robust management of missing data or formatting issues.

## 🚀 Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt

```

2. Launch the application:

```bash
streamlit run app.py

```

## 📊 Required Data Format

The input Excel or CSV file should contain the following columns:

| Column | Description | Required |
| --- | --- | --- |
| **Easting** | UTM East coordinate | ✅ Yes |
| **Northing** | UTM North coordinate | ✅ Yes |
| **Name** | Point name (e.g., Cave Name) | No |
| **Elevation** | Altitude in meters | No |
| **ID** | Provincial Registry or ID | No |
| **Area** | Reference region/area | No |
| **Municipality** | Name of the town/city | No |

## 🗺️ Supported UTM Zones

While the app is flexible, it is pre-configured for common European and Italian zones:

* **32N**: Northwest Italy / Central Europe
* **33N**: Central-East Italy / Eastern Europe
* **34N**: Southeast Italy / Balkans
* Supports Southern Hemisphere zones (e.g., **32S**, **33S**) via the selection menu.

## 📝 How to Use

1. **Prepare**: Create an Excel/CSV file with your UTM coordinates.
2. **Launch**: Run the app using `streamlit run app.py`.
3. **Upload**: Drag and drop your file into the interface.
4. **Configure**: Select the correct UTM zone and hemisphere for your data.
5. **Verify**: Check the data preview and point locations on the interactive map.
6. **Convert**: Click the "Generate GPX" button.
7. **Download**: Save the resulting file to your device.

## 🛠️ Tech Stack

* **Streamlit**: Web interface and interactivity.
* **Pandas**: Data parsing and manipulation.
* **PyProj**: High-precision coordinate transformation (Transformer).
* **GPXpy**: GPX file structure generation.
* **OpenPyXL**: Excel file engine.

## 📄 License

Open-source project for educational and professional use.
