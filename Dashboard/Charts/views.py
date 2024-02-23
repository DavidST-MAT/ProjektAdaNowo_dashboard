from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from influxdb_client import InfluxDBClient, Point
from django.views.decorators.csrf import csrf_exempt
import datetime
import pandas as pd
from datetime import timedelta


def index(request):

    influxdb_settings = settings.INFLUXDB_SETTINGS
    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")  # for testing on local machine

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "SetValues" and r["_field"] == "PerformanceMeasure")
    |> group(columns: ["_field"])
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 10)"""

    # Execute the Flux query and store the result in tables
    tables = query_api.query(query_Actual_Values, org="MAT")
    performance_measure = []
    performance_measure_time = []


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            performance_measure.append(value)
            performance_measure_time.append([time])

    print(performance_measure)

    performance_measure_context = {'performance_measure': performance_measure, 'performance_measure_time': performance_measure_time}



    return render(request, 'Charts/performance.html', performance_measure_context)



def getPerformanceMeasureOneHour(request):
    performance_measure = []

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "SetValues" and r["_field"] == "PerformanceMeasure")
    |> group(columns: ["_field"])
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)"""

    tables = query_api.query(query_Actual_Values, org="MAT")


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            performance_measure.append(value)


    return JsonResponse(performance_measure, safe=False)



def getPerformanceMeasureFourHour(request):
    performance_measure = []

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "SetValues" and r["_field"] == "PerformanceMeasure")
    |> group(columns: ["_field"])
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)"""

    tables = query_api.query(query_Actual_Values, org="MAT")


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            performance_measure.append(value)


    return JsonResponse(performance_measure, safe=False)




##################### ENERGIEWERTE ###################


# view for "Energiewerte"
def energiewerte(request):

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")  # for testing on local machine

    query_api = client_influxdb.query_api()

    # Query for the data
    query_Actual_Values = """from(bucket: "AdaNowoTest")
        |> range(start: -1h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues")
        |> filter(fn: (r) => r["_field"] == "Energy")
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables = query_api.query(query_Actual_Values, org="MAT")
    energy_consumption = []
    energy_consumption_time = []


    for table in tables:
        print(table)
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            if value == None: 
                value = 0
            energy_consumption.append(value)
            formatted_datetime = time.strftime("%H:%M:%S")
            energy_consumption_time.append(formatted_datetime)

    print(energy_consumption)
    print(energy_consumption_time)

    energy_consumption_context = {'energy_consumption': energy_consumption, 'energy_consumption_time': energy_consumption_time}

    return render(request, 'Charts/energiewerte.html', energy_consumption_context)



# Function for updating the "Energieverbrauch"- Charts with 1min interval
def get_energy_consumption_one_hour_update(request):

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "Energy")
        |> group(columns: ["_field"])
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 1)"""

    tables = query_api.query(query_Actual_Values, org="MAT")


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
      
    print(value)
    return JsonResponse(value, safe=False)



# Function for slecting time-selector "1h"
def get_energy_consumption_one_hour(request):
    energy_consumption_one = []
    energy_consumption_one_time = []

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
        |> range(start: -1h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues")
        |> filter(fn: (r) => r["_field"] == "Energy")
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    tables = query_api.query(query_Actual_Values, org="MAT")


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            if value == None: 
                value = 0
            energy_consumption_one.append(value)
            formatted_datetime = time.strftime("%H:%M:%S")
            energy_consumption_one_time.append(formatted_datetime)

    print(energy_consumption_one)
    print(energy_consumption_one_time)

    energy_consumption_context = {'energy_consumption_one': energy_consumption_one, 'energy_consumption_one_time': energy_consumption_one_time}

    return JsonResponse(energy_consumption_context, safe=False)



# Function for slecting time-selector "4h"
def get_energy_consumption_four_hour(request):
    energy_consumption_four = []
    energy_consumption_four_time = []

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
        |> range(start: -4h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues")
        |> filter(fn: (r) => r["_field"] == "Energy")
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    tables = query_api.query(query_Actual_Values, org="MAT")


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            if value == None: 
                value = 0
            energy_consumption_four.append(value)
            formatted_datetime = time.strftime("%H:%M:%S")
            energy_consumption_four_time.append(formatted_datetime)

    print(energy_consumption_four)
    print(energy_consumption_four_time)

    energy_consumption_context = {'energy_consumption_four': energy_consumption_four, 'energy_consumption_four_time': energy_consumption_four_time}

    return JsonResponse(energy_consumption_context, safe=False)


#######################################





def umweltwerte(request):

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")  # for testing on local machine

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "SetValues" and r["_field"] == "PerformanceMeasure")
    |> group(columns: ["_field"])
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 10)"""

    # Execute the Flux query and store the result in tables
    tables = query_api.query(query_Actual_Values, org="MAT")
    room_temperature = []
    room_temperature_time = []


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            room_temperature.append(value)
            room_temperature_time.append([time])

    print(room_temperature)

    room_temperature_context = {'room_temperature': room_temperature, 'room_temperature_time': room_temperature_time}

    return render(request, 'Charts/umweltwerte.html', room_temperature_context)



def get_temperatur_one_hour(request):

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")  # for testing on local machine

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "SetValues" and r["_field"] == "PerformanceMeasure")
    |> group(columns: ["_field"])
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)"""

    # Execute the Flux query and store the result in tables
    tables = query_api.query(query_Actual_Values, org="MAT")
    room_temperature = []
    room_temperature_time = []


    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            time = record.values["_time"]
            room_temperature.append(value)
            room_temperature_time.append(time)

    print(room_temperature)

    room_temperature_context = [value, time]



    return JsonResponse(room_temperature_context, safe=False)