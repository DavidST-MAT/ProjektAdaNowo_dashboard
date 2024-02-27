from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from influxdb_client import InfluxDBClient, Point
from django.views.decorators.csrf import csrf_exempt
import datetime
import pandas as pd
from datetime import datetime, timedelta
from statistics import median


def index(request):

    influxdb_settings = settings.INFLUXDB_SETTINGS
    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")  # for testing on local machine

    query_api = client_influxdb.query_api()

    query_performance_measure = """from(bucket: "AdaNowoTest")
        |> range(start: -1h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues")
        |> filter(fn: (r) => r["_field"] == "PerformanceMeasure")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_performance_measure = query_api.query(query_performance_measure, org="MAT")
    performance_measure = []
    performance_measure_time = []


    for table_performance_measure in tables_performance_measure:
        for record_performance_measure in table_performance_measure.records:
            pm_value = record_performance_measure.values["_value"]
            pm_time = record_performance_measure.values["_time"]
            if pm_value == None: 
                pm_value = 0
            performance_measure.append(pm_value)
            pm_time_updated = pm_time + timedelta(hours=1)
            pm_formatted_datetime = pm_time_updated.strftime("%H:%M:%S")
            performance_measure_time.append(pm_formatted_datetime)

    print(performance_measure)
    print(performance_measure_time)



    # Query for the data
    query_energy_consumption = """from(bucket: "AdaNowoTest")
        |> range(start: -1h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues")
        |> filter(fn: (r) => r["_field"] == "Energy")
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_energy_consumption = query_api.query(query_energy_consumption, org="MAT")
    energy_consumption = []
    energy_consumption_time = []


    for table_energy_consumption in tables_energy_consumption:
        print(table_energy_consumption)
        for record_energy_consumption in table_energy_consumption.records:
            ec_value = record_energy_consumption.values["_value"]
            ec_time = record_energy_consumption.values["_time"]
            if ec_value == None: 
                ec_value = 0
            energy_consumption.append(ec_value)
            ec_updated_time = ec_time + timedelta(hours=1)
            ec_formatted_datetime = ec_updated_time.strftime("%H:%M:%S")
            energy_consumption_time.append(ec_formatted_datetime)

    print(energy_consumption)
    print(energy_consumption_time)





    area_weights = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_area_weight = f'''
        from(bucket: "LabData")
        |> range(start: -1h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "area_weight_1" or r["_field"] == "area_weight_2" or r["_field"] == "area_weight_3")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_area_weight = query_api.query(query_area_weight, org="MAT")
        area_weight = []
        area_weight_time = []
        

        for table_area_weight in tables_area_weight:
            print(table_area_weight)
            for record_area_weight in table_area_weight.records:
                aw_value = record_area_weight.values["_value"]
                aw_time = record_area_weight.values["_time"]
                if aw_value == None: 
                    aw_value = 0
                area_weight.append(aw_value)
                aw_updated_time = aw_time + timedelta(hours=1)
                aw_formatted_datetime = aw_updated_time.strftime("%H:%M:%S")
                area_weight_time.append(aw_formatted_datetime)

        area_weights.append(area_weight)

    print(area_weights)
    print(area_weight_time)
    print(len(area_weight_time))





    context = {'performance_measure': performance_measure, 'performance_measure_time': performance_measure_time, 'energy_consumption': energy_consumption, 'energy_consumption_time': energy_consumption_time, 'area_weights': area_weights, 'area_weight_time': area_weight_time}

    return render(request, 'Charts/performance.html', context)








################################ TEST UPDATING ######################################

# Function for updating the Charts 
def updateChartOneMinute(request):
    updated_values = []

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")

    query_api = client_influxdb.query_api()


    ### Updating PerformanceMeasurement ###
    query_performance = """from(bucket: "AdaNowoTest")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["_field"] == "PerformanceMeasure")
    |> group(columns: ["_field"])
    |> last()"""

    tables = query_api.query(query_performance, org="MAT")

    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            updated_values.append(value)



    ### Updating Energieverbrauch ###
    query_energy = """from(bucket: "AdaNowoTest")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "Energy")
        |> group(columns: ["_field"])
        |> last()"""

    tables = query_api.query(query_energy, org="MAT")

    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            updated_values.append(value)



    ### Updating AreaWeight ###
    query_area = """from(bucket: "LabData")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "area_weight_1" or r["_field"] == "area_weight_2" or r["_field"] == "area_weight_3")
        |> group(columns: ["_field"])
        |> last()"""
    
    tables = query_api.query(query_area, org="MAT")
    area_weight = []
    
    for table in tables:
        for record in table.records:
            value = record.values["_value"]
            area_weight.append(value)

    max_area = max(area_weight)
    min_area = min(area_weight)
    median_area = median(area_weight)

    updated_values.append(max_area)
    updated_values.append(min_area)
    updated_values.append(median_area)
 
    print(updated_values)
    
    return JsonResponse(updated_values, safe=False)








#######################################################################################




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






def getPerformanceMeasureOneHour(request):
    performance_measure = []

    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")

    query_api = client_influxdb.query_api()

    query_Actual_Values = """from(bucket: "AdaNowoTest")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["_field"] == "PerformanceMeasure")
    |> group(columns: ["_field"])
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)"""

    tables = query_api.query(query_Actual_Values, org="MAT")

    for table in tables:
        for record in table.records:
            value = record.values["_value"]

    return JsonResponse(value, safe=False)


####################################################################################################













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