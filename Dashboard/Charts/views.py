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
        |> range(start: -2h, stop: now())
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



    tensile_force_md_all = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_tables_tensile_md = f'''
        from(bucket: "LabData")
        |> range(start: -2h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "maximum_tensile_force_md_1" or r["_field"] == "maximum_tensile_force_md_2" or r["_field"] == "maximum_tensile_force_md_3")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_tensile_force_md = query_api.query(query_tables_tensile_md, org="MAT")
        tensile_force_md = []
  
        

        for table_tensile_force_md in tables_tensile_force_md:
            print(table_tensile_force_md)
            for record_tensile_force_md in table_tensile_force_md.records:
                tf_md_value = record_tensile_force_md.values["_value"]
                if tf_md_value == None: 
                    tf_md_value = 0
                tensile_force_md.append(tf_md_value)


        tensile_force_md_all.append(tensile_force_md)

    print(tensile_force_md_all)


    tensile_force_cd_all = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_tables_tensile_cd = f'''
        from(bucket: "LabData")
        |> range(start: -2h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "maximum_tensile_force_cd_1" or r["_field"] == "maximum_tensile_force_cd_2" or r["_field"] == "maximum_tensile_force_cd_3")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_tensile_force_cd = query_api.query(query_tables_tensile_cd, org="MAT")
        tensile_force_cd = []
  
        

        for table_tensile_force_cd in tables_tensile_force_cd:
            print(table_tensile_force_cd)
            for record_tensile_force_cd in table_tensile_force_cd.records:
                tf_cd_value = record_tensile_force_cd.values["_value"]
                if tf_cd_value == None: 
                    tf_cd_value = 0
                tensile_force_cd.append(tf_cd_value)


        tensile_force_cd_all.append(tensile_force_cd)

    print(tensile_force_cd_all)
  




    context = {'performance_measure': performance_measure, 'performance_measure_time': performance_measure_time, 'energy_consumption': energy_consumption, 'energy_consumption_time': energy_consumption_time, 'area_weights': area_weights, 'area_weight_time': area_weight_time, 'tensile_force_md_all': tensile_force_md_all, 'tensile_force_cd_all': tensile_force_cd_all}

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

    if tables == []:
        updated_values.append(0)
    else:
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

    if tables == []:
        updated_values.append(0)
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values.append(value)



    ### Updating AreaWeight ###
    query_area = """from(bucket: "LabData")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "area_weight_1" or r["_field"] == "area_weight_2" or r["_field"] == "area_weight_3" or r["_field"] == "maximum_tensile_force_md_1" or r["_field"] == "maximum_tensile_force_md_2" or r["_field"] == "maximum_tensile_force_md_3" or r["_field"] == "maximum_tensile_force_cd_1" or r["_field"] == "maximum_tensile_force_cd_2" or r["_field"] == "maximum_tensile_force_cd_3")
        |> group(columns: ["_field"])
        |> last()"""
    
    tables = query_api.query(query_area, org="MAT")
    lab_values = []
    
    if tables == []:
        updated_values.append(0)
        updated_values.append(0)
        updated_values.append(0)
        updated_values.append(0)
        updated_values.append(0)
        updated_values.append(0)
        updated_values.append(0)
        updated_values.append(0)
        updated_values.append(0)
        
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                lab_values.append(value)


        area_weight = lab_values[:3]
        tensile_cd = lab_values[3:6]
        tensile_md = lab_values[6:]

        max_area = max(area_weight)
        min_area = min(area_weight)
        median_area = median(area_weight)

        max_tensile_cd = max(tensile_cd)
        min_tensile_cd = min(tensile_cd)
        median_tensile_cd = median(tensile_cd)

        max_tensile_md = max(tensile_md)
        min_tensile_md = min(tensile_md)
        median_tensile_md = median(tensile_md)

        updated_values.append(max_area)
        updated_values.append(min_area)
        updated_values.append(median_area)
        updated_values.append(max_tensile_cd)
        updated_values.append(min_tensile_cd)
        updated_values.append(median_tensile_cd)
        updated_values.append(max_tensile_md)
        updated_values.append(min_tensile_md)
        updated_values.append(median_tensile_md)


    

    print(updated_values)
    
    return JsonResponse(updated_values, safe=False)








#######################################################################################







































def time(request):


    client_influxdb = InfluxDBClient(url="http://localhost:8086", token="Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==", org="MAT")  # for testing on local machine

    query_api = client_influxdb.query_api()

    query_performance_measure = """from(bucket: "AdaNowoTest")
        |> range(start: -4h, stop: now())
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
        |> range(start: -4h, stop: now())
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
        |> range(start: -4h, stop: now())
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



    tensile_force_md_all = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_tables_tensile_md = f'''
        from(bucket: "LabData")
        |> range(start: -4h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "maximum_tensile_force_md_1" or r["_field"] == "maximum_tensile_force_md_2" or r["_field"] == "maximum_tensile_force_md_3")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_tensile_force_md = query_api.query(query_tables_tensile_md, org="MAT")
        tensile_force_md = []
  
        

        for table_tensile_force_md in tables_tensile_force_md:
            print(table_tensile_force_md)
            for record_tensile_force_md in table_tensile_force_md.records:
                tf_md_value = record_tensile_force_md.values["_value"]
                if tf_md_value == None: 
                    tf_md_value = 0
                tensile_force_md.append(tf_md_value)


        tensile_force_md_all.append(tensile_force_md)

    print(tensile_force_md_all)


    tensile_force_cd_all = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_tables_tensile_cd = f'''
        from(bucket: "LabData")
        |> range(start: -4h, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "maximum_tensile_force_cd_1" or r["_field"] == "maximum_tensile_force_cd_2" or r["_field"] == "maximum_tensile_force_cd_3")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_tensile_force_cd = query_api.query(query_tables_tensile_cd, org="MAT")
        tensile_force_cd = []
  
        

        for table_tensile_force_cd in tables_tensile_force_cd:
            print(table_tensile_force_cd)
            for record_tensile_force_cd in table_tensile_force_cd.records:
                tf_cd_value = record_tensile_force_cd.values["_value"]
                if tf_cd_value == None: 
                    tf_cd_value = 0
                tensile_force_cd.append(tf_cd_value)


        tensile_force_cd_all.append(tensile_force_cd)

    print(tensile_force_cd_all)
  




    context = {'performance_measure': performance_measure, 'performance_measure_time': performance_measure_time, 'energy_consumption': energy_consumption, 'energy_consumption_time': energy_consumption_time, 'area_weights': area_weights, 'area_weight_time': area_weight_time, 'tensile_force_md_all': tensile_force_md_all, 'tensile_force_cd_all': tensile_force_cd_all}


    return render(request, 'Charts/time.html', context)