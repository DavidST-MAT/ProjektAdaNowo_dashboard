from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse, QueryDict
from influxdb_client import InfluxDBClient, Point
from django.views.decorators.csrf import csrf_exempt
import datetime
import pandas as pd
from datetime import datetime, timedelta
from statistics import median
import os


# Influx Configuration
class InfluxDBConfig:

    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        #self.token = os.getenv("INFLUXDB_TOKEN", "Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==")
        self.token = os.getenv("INFLUXDB_TOKEN", "L43SXxiyt-jYReLa0NdsUgvIvCSk_BsC7shKlf2HXiboELJsVYbWEQfv57-Ml0GX58m1CjateBgEBwFKEtK4mQ==")
        self.org = os.getenv("INFLUXDB_ORG", "MAT")



def index(request):

    get_hours = request.GET.get('value')
    if get_hours == None:
        get_hours = 1
    query_hours = f"-{get_hours}h"
    print(query_hours)

    influxdb_config = InfluxDBConfig()

    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org) 

    query_api = client_influxdb.query_api()

    ############################################################################################################

    ### NonwovenUnevenness ###
    query_nonwoven_uvenness = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "NonwovenUnevenness")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_nonwoven_uvenness = query_api.query(query_nonwoven_uvenness, org=influxdb_config.org)
    nonwoven_uvenness = []
    nonwoven_uvenness_time = []


    for table_nonwoven_uvenness in tables_nonwoven_uvenness:
        for record_nonwoven_uvenness in table_nonwoven_uvenness.records:
            nu_value = record_nonwoven_uvenness.values["_value"]
            nu_time = record_nonwoven_uvenness.values["_time"]
            if nu_value == None: 
                nu_value = 0
            nonwoven_uvenness.append(nu_value)
            nu_time_updated = nu_time + timedelta(hours=1)
            nu_formatted_datetime = nu_time_updated.strftime("%H:%M:%S")
            nonwoven_uvenness_time.append(nu_formatted_datetime)


    if nonwoven_uvenness != [] and nonwoven_uvenness[-1] == 0:
        nonwoven_uvenness[-1] = nonwoven_uvenness[-2]



    ############################################################################################################


    ### LinePowerConsumption ###
    query_energy_consumption = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "LinePowerConsumption")
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_energy_consumption = query_api.query(query_energy_consumption, org=influxdb_config.org)
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

    if energy_consumption != [] and energy_consumption[-1] == 0:
        energy_consumption[-1] = energy_consumption[-2]

  


    ############################################################################################################


    ### Ambient Temperatur ###
    query_ambient_temperature = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "AmbientTemperature")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_ambient_temperature = query_api.query(query_ambient_temperature, org=influxdb_config.org)
    ambient_temperature = []
    ambient_temperature_time = []


    for table_ambient_temperature in tables_ambient_temperature:
        for record_ambient_temperature in table_ambient_temperature.records:
            at_value = record_ambient_temperature.values["_value"]
            at_time = record_ambient_temperature.values["_time"]
            if at_value == None: 
                at_value = 0
            ambient_temperature.append(at_value)
            at_time_updated = at_time + timedelta(hours=1)
            at_formatted_datetime = at_time_updated.strftime("%H:%M:%S")
            ambient_temperature_time.append(at_formatted_datetime)

    if ambient_temperature != [] and ambient_temperature[-1] == 0:
        ambient_temperature[-1] = ambient_temperature[-2]

  
 

    ##############################################################################################################


    ### Lab Values ###
    area_weights = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_area_weight = f'''
        from(bucket: "LabValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "AreaWeight_AW1" or r["_field"] == "AreaWeight_AW2" or r["_field"] == "AreaWeight_AW3")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_area_weight = query_api.query(query_area_weight, org=influxdb_config.org)
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





    tensile_force_md_all = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_tables_tensile_md = f'''
        from(bucket: "LabValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "TensileStrength_MD1" or r["_field"] == "TensileStrength_MD2" or r["_field"] == "TensileStrength_MD3" or r["_field"] == "TensileStrength_MD4" or r["_field"] == "TensileStrength_MD5")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_tensile_force_md = query_api.query(query_tables_tensile_md, org=influxdb_config.org)
        tensile_force_md = []
  
        

        for table_tensile_force_md in tables_tensile_force_md:
            print(table_tensile_force_md)
            for record_tensile_force_md in table_tensile_force_md.records:
                tf_md_value = record_tensile_force_md.values["_value"]
                if tf_md_value == None: 
                    tf_md_value = 0
                tensile_force_md.append(tf_md_value)


        tensile_force_md_all.append(tensile_force_md)




    tensile_force_cd_all = []
    aggregation_fns = ["min", "max", "mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_tables_tensile_cd = f'''
        from(bucket: "LabValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "TensileStrength_CD1" or r["_field"] == "TensileStrength_CD2" or r["_field"] == "TensileStrength_CD3" or r["_field"] == "TensileStrength_CD4" or r["_field"] == "TensileStrength_CD5")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: {aggregation_fn})
        |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_tensile_force_cd = query_api.query(query_tables_tensile_cd, org=influxdb_config.org)
        tensile_force_cd = []
  
        

        for table_tensile_force_cd in tables_tensile_force_cd:
            print(table_tensile_force_cd)
            for record_tensile_force_cd in table_tensile_force_cd.records:
                tf_cd_value = record_tensile_force_cd.values["_value"]
                if tf_cd_value == None: 
                    tf_cd_value = 0
                tensile_force_cd.append(tf_cd_value)


        tensile_force_cd_all.append(tensile_force_cd)


  

    ############################################################################################################


    ### Humidty Environment ###
    query_humidity_environment = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "RelativeHumidityEnvironment")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_humidity_environment = query_api.query(query_humidity_environment, org=influxdb_config.org)
    humidity_environment = []
    humidity_environment_time = []


    for table_humidity_environment in tables_humidity_environment:
        for record_humidity_environment in table_humidity_environment.records:
            he_value = record_humidity_environment.values["_value"]
            he_time = record_humidity_environment.values["_time"]
            if he_value == None: 
                he_value = 0
            humidity_environment.append(he_value)
            he_time_updated = he_time + timedelta(hours=1)
            he_formatted_datetime = he_time_updated.strftime("%H:%M:%S")
            humidity_environment_time.append(he_formatted_datetime)


    if humidity_environment != [] and humidity_environment[-1] == 0:
        humidity_environment[-1] = humidity_environment[-2]


    
        


    ############################################################################################################


    ### Economics ###
        
    fibre_costs = 1.20 # € per kg
    energy_costs_x = 0.28 # € per kWh
    selling_price = 2.10 # € per sqm
    floor_quality_weight = 50.0

    query_energy_costs = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "LinePowerConsumption")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_energy_costs = query_api.query(query_energy_costs, org=influxdb_config.org)
    energy_costs = []
    energy_costs_time = []


    for table_energy_costs in tables_energy_costs:
        for record_energy_costs in table_energy_costs.records:
            ec_value = record_energy_costs.values["_value"]
            ec_time = record_energy_costs.values["_time"]
            if ec_value == None: 
                ec_value = 0
            else:
                ec_value= ec_value * 0.28
            energy_costs.append(ec_value)
            ec_time_updated = ec_time + timedelta(hours=1)
            ec_formatted_datetime = ec_time_updated.strftime("%H:%M:%S")
            energy_costs_time.append(ec_formatted_datetime)


    if energy_costs != [] and energy_costs[-1] == 0:
        energy_costs[-1] = energy_costs[-2]



    print(energy_costs)



    context = {
        'nonwoven_uvenness': nonwoven_uvenness, 
        'nonwoven_uvenness_time': nonwoven_uvenness_time, 
        'energy_consumption': energy_consumption, 
        'energy_consumption_time': energy_consumption_time,
        'ambient_temperature': ambient_temperature,
        'ambient_temperature_time': ambient_temperature_time, 
        'area_weights': area_weights, 
        'area_weight_time': area_weight_time, 
        'tensile_force_md_all': tensile_force_md_all, 
        'tensile_force_cd_all': tensile_force_cd_all,
        'humidity_environment': humidity_environment,
        'humidity_environment_time': humidity_environment_time,
        'energy_costs': energy_costs,
        'energy_costs_time': energy_costs_time
        }

    return render(request, 'Charts/performance.html', context)






# Function for updating the Charts 
def updateChartOneMinute(request):
    updated_values = []

    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)

    query_api = client_influxdb.query_api()


    ### Updating Nonwoven Unevenness ###
    query_performance = """from(bucket: "AgentValues")
    |> range(start: -1m, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "NonwovenUnevenness" and r["Iteration"] == "-1")
    |> group(columns: ["_field"])
    |> last()"""

    tables = query_api.query(query_performance, org=influxdb_config.org)

    if tables == []:
        updated_values.append(0)
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values.append(value)



    ### Updating Line Power Consumption ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "LinePowerConsumption" and r["Iteration"] == "-1")
        |> group(columns: ["_field"])
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values.append(0)
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values.append(value)


    ### Updating Ambient Temperature ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "AmbientTemperature" and r["Iteration"] == "-1")
        |> group(columns: ["_field"])
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values.append(0)
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values.append(value)



    ### Updating AreaWeight ###
    query_area = """from(bucket: "LabValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "AreaWeight_AW1" or r["_field"] == "AreaWeight_AW2" or r["_field"] == "AreaWeight_AW3" or r["_field"] == "TensileStrength_MD1" or r["_field"] == "TensileStrength_MD2" or r["_field"] == "TensileStrength_MD3" or r["_field"] == "TensileStrength_MD4" or r["_field"] == "TensileStrength_MD5" or r["_field"] == "TensileStrength_CD1" or r["_field"] == "TensileStrength_CD2" or r["_field"] == "TensileStrength_CD3" or r["_field"] == "TensileStrength_CD4" or r["_field"] == "TensileStrength_CD5")
        |> group(columns: ["_field"])
        |> last()"""
    
    tables = query_api.query(query_area, org=influxdb_config.org)
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


    ### Updating Humidty Environment ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "RelativeHumidityEnvironment" and r["Iteration"] == "-1")
        |> group(columns: ["_field"])
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values.append(0)
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values.append(value)


    

    #print(updated_values)
    
    return JsonResponse(updated_values, safe=False)





