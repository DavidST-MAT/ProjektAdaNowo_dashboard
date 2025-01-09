# Django Realtime Dashboard with Chart.js and InfluxDB

This project is a Django application that provides a real-time dashboard. The dashboard displays various **line charts** created using  **Chart.js** . The data visualized in the charts is fetched from an **InfluxDB** and updated in real-time.

The goal of this project is to deliver a modern and interactive data visualization platform by leveraging powerful technologies like Django, Chart.js, and InfluxDB.

## Features

Key features of this project include:

* **Real-time data visualization** : Continuous updates to charts without manual page refreshes.
* **Integration with InfluxDB** : Fast and efficient querying of time-series data.
* **Responsive design** : Optimized display across various devices.
* **Time range selection** : Users can choose from various time ranges to customize the data displayed in the charts.

## Setup

Follow these steps to set up the project on your local machine and make sure you are using a virtual environment for running the application or use a docker container (recommended):

### Prerequisites

* **Python 3.8+** : Make sure Python is installed on your system.
* **InfluxDB** : An instance of InfluxDB should be running and accessible.
* **Django** : Installed via `pip` or added as a dependency in `requirements.txt`.

### Installation (local)

Your y-axis might be offtime, when your are not using docker internal time.

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
2. **Set up environment variables**: Create a `.env` file and set the `InfluxDB credentials`:
3. **Start the development server**:

   ```bash
   python manage.py runserver 
   ```

## Running with Docker

If you'd like to run the application within a Docker container, you can use the provided Dockerfile. Follow these steps to start the application with Docker:

1. **Build the Docker image**:

   Build the Docker image with the following command:

   ```bash
   docker build -t django-dashboard .  
   ```
2. **Run the Docker container**:

   Start the Docker container that contains the Django application:

   ```bash
   docker run -p 8086:8086 django-dashboard  
   ```

   This command runs the container and maps port 8086 from the container to port 8086 on your host. You can now access the Django application through your browser or via API requests.

The application will be available at `http://localhost:8086`.
