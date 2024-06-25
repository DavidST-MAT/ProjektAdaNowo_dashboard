from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse, QueryDict
from influxdb_client import InfluxDBClient, Point
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
import pandas as pd
from datetime import datetime, timedelta
from statistics import median
import os


# Config variables
fibre_costs = 1.20 # € per kg
energy_costs_x = 0.28 # € per kWh
selling_price = 2.10 # € per sqm
floor_quality_weight = 50.0
unevenness_signal_mean = 10.0
unevenness_signal_std = 2.0

# Time selection
aggregate_time = {
    '1h': '1m',
    '3h': '1m',
    '6h': '1m',
    '12h': '1m',
    '1d': '10m',
    '7d': '1h',
    '30d': '1h'
}

time_select_empty_table = {
  '1h': 1,
  '3h': 3,
  '6h': 6,
  '12h': 12,
  '1d': 24,
  '7d': 168,
  '30d': 720
}


# Influx Configuration
class InfluxDBConfig:

    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        #self.token = os.getenv("INFLUXDB_TOKEN", "Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==")
        self.token = os.getenv("INFLUXDB_TOKEN", "L43SXxiyt-jYReLa0NdsUgvIvCSk_BsC7shKlf2HXiboELJsVYbWEQfv57-Ml0GX58m1CjateBgEBwFKEtK4mQ==")
        self.org = os.getenv("INFLUXDB_ORG", "MAT")


############################################################################################################

### NonwovenUnevenness ### Card Floor Unevenness ###
def get_nonwoven_unevenness(chart, selected_time, influxdb_config, query_api):

    query_time_modified = f"-{selected_time}"

    query_nonwoven_uvenness = f"""from(bucket: "AgentValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "NonwovenUnevenness")
        |> filter(fn: (r) => r["Unit"] == "-")
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
        |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_nonwoven_uvenness = query_api.query(query_nonwoven_uvenness, org=influxdb_config.org)
    nonwoven_uvenness = []
    nonwoven_uvenness2 = []
    nonwoven_uvenness_time = []

    for table_nonwoven_uvenness in tables_nonwoven_uvenness:
        for record_nonwoven_uvenness in table_nonwoven_uvenness.records:
            nu_value = record_nonwoven_uvenness.values["_value"]
            nu_time = record_nonwoven_uvenness.values["_time"]
            nonwoven_uvenness.append(nu_value)
            nonwoven_uvenness2.append(nu_value)

            nu_time_updated = nu_time + timedelta(hours=2)
            if aggregate_time[selected_time] == "1h":
                nu_formatted_datetime = nu_time_updated.strftime("%d-%m %H:%M")
            else:
                nu_formatted_datetime = nu_time_updated.strftime("%H:%M")
            nonwoven_uvenness_time.append(nu_formatted_datetime)

    if nonwoven_uvenness != [] and nonwoven_uvenness[-1] == 0:
        nonwoven_uvenness[-1] = nonwoven_uvenness[-2]
    if nonwoven_uvenness != [] and nonwoven_uvenness[0] == 0:
        nonwoven_uvenness[0] = nonwoven_uvenness[1]

    if nonwoven_uvenness == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            nonwoven_uvenness.append("NaN")
            nonwoven_uvenness2.append(None)

    if nonwoven_uvenness_time == []:
        time_now = datetime.now()
        nonwoven_uvenness_time = []

        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            time = time_now - timedelta(minutes=i)
            if aggregate_time[selected_time] == "1h":
                nonwoven_uvenness_time.append(time.strftime("%d-%m %H:%M"))
            else:
                nonwoven_uvenness_time.append(time.strftime("%H:%M"))
    
    #nonwoven_uvenness.pop()
    #nonwoven_uvenness_time.pop()

    if chart == "NonwovenUnevennes":
        nonwoven_uvenness = [x if x is not None else "NaN" for x in nonwoven_uvenness]
        return nonwoven_uvenness, nonwoven_uvenness_time
    elif chart == "CardFloorEvenness":
        scaled_signal = [(x - unevenness_signal_mean) / unevenness_signal_std if x is not None else "NaN" for x in nonwoven_uvenness2]
        card_floor_evenness = [x * floor_quality_weight if x != "NaN" else "NaN" for x in scaled_signal]
        return card_floor_evenness, nonwoven_uvenness_time


############################################################################################################

### AmbientTemperature ###
def get_ambient_temperature(selected_time, influxdb_config, query_api):

    query_time_modified = f"-{selected_time}"

    query_ambient_temperature = f"""from(bucket: "AgentValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "AmbientTemperature")
        |> filter(fn: (r) => r["Unit"] == "°C")
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
        |> yield(name: "last")"""

    tables_ambient_temperature = query_api.query(query_ambient_temperature, org=influxdb_config.org)
    ambient_temperature = []
    ambient_temperature_time = []


    for table_ambient_temperature in tables_ambient_temperature:
        for record_ambient_temperature in table_ambient_temperature.records:
            at_value = record_ambient_temperature.values["_value"]
            at_time = record_ambient_temperature.values["_time"]

            # if at_value == None: 
            #     at_value = 0.0

            ambient_temperature.append(at_value)
            at_time_updated = at_time + timedelta(hours=2)
            if aggregate_time[selected_time] == "1h":
                at_formatted_datetime = at_time_updated.strftime("%d-%m %H:%M")
            else:
                at_formatted_datetime = at_time_updated.strftime("%H:%M")
            ambient_temperature_time.append(at_formatted_datetime)

    if ambient_temperature != [] and ambient_temperature[-1] == 0:
        ambient_temperature[-1] = ambient_temperature[-2]
    if ambient_temperature != [] and ambient_temperature[0] == 0:
        ambient_temperature[0] = ambient_temperature[1]

    if ambient_temperature == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            ambient_temperature.append("NaN")


    if ambient_temperature_time == []:
        time_now = datetime.now()
        ambient_temperature_time = [] # ?

        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            time = time_now - timedelta(minutes=i)
            if aggregate_time[selected_time] == "1h":
                ambient_temperature_time.append(time.strftime("%d-%m %H:%M"))
            else:
                ambient_temperature_time.append(time.strftime("%H:%M"))

    ambient_temperature = [x if x is not None else "NaN" for x in ambient_temperature]



    ######################################################################################

    query_humidity_environment = f"""from(bucket: "AgentValues")
    |> range(start: {query_time_modified}, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
    |> filter(fn: (r) => r["_field"] == "RelativeHumidityEnvironment")
    |> filter(fn: (r) => r["Unit"] == "%")
    |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
    |> yield(name: "last")"""

    # Execute the Flux query and store the result in tables
    tables_humidity_environment = query_api.query(query_humidity_environment, org=influxdb_config.org)
    humidity_environment = []
    humidity_environment_time = []


    for table_humidity_environment in tables_humidity_environment:
        for record_humidity_environment in table_humidity_environment.records:
            he_value = record_humidity_environment.values["_value"]
            he_time = record_humidity_environment.values["_time"]

            #if he_value == None: 
            #    he_value = 0.0

            humidity_environment.append(he_value)

            he_time_updated = he_time + timedelta(hours=2)
            if aggregate_time[selected_time] == "1h":
                he_formatted_datetime = he_time_updated.strftime("%d-%m %H:%M")
            else:
                he_formatted_datetime = he_time_updated.strftime("%H:%M")
            humidity_environment_time.append(he_formatted_datetime)


    if humidity_environment != [] and humidity_environment[-1] == 0:
        humidity_environment[-1] = humidity_environment[-2]
    if humidity_environment != [] and humidity_environment[0] == 0:
        humidity_environment[0] = humidity_environment[1]


    if humidity_environment == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            humidity_environment.append("NaN")


    if humidity_environment_time == []:
        time_now = datetime.now()
        humidity_environment_time = []

        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            time = time_now - timedelta(minutes=i)
            if aggregate_time[selected_time] == "1h":
                humidity_environment_time.append(time.strftime("%d-%m %H:%M"))
            else:
                humidity_environment_time.append(time.strftime("%H:%M"))
    
    humidity_environment = [x if x is not None else "NaN" for x in humidity_environment]

    return [ambient_temperature, humidity_environment], ambient_temperature_time


############################################################################################################

### Laboratory Values ###
def get_laboratory_values(selected_time, influxdb_config, query_api):
    query_time_modified = f"-{selected_time}"

    #aggregation_fns = ["min", "max", "mean"]
    aggregation_fns = ["mean"]

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_area_weight = f'''
        from(bucket: "AgentValues")
            |> range(start: {query_time_modified}, stop: now())
            |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
            |> filter(fn: (r) => r["_field"] == "AreaWeightLane1" or r["_field"] == "AreaWeightLane2" or r["_field"] == "AreaWeightLane3")
            |> group(columns: ["_measurement"])
            |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: {aggregation_fn})
            |> yield(name: "min")
        '''

        # Execute the Flux query and store the result in tables
        tables_area_weight = query_api.query(query_area_weight, org=influxdb_config.org)
        area_weight = []
        area_weight_time = []
        
        for table_area_weight in tables_area_weight:
            for record_area_weight in table_area_weight.records:
                aw_value = record_area_weight.values["_value"]
                aw_time = record_area_weight.values["_time"]
                area_weight.append(aw_value)
                aw_updated_time = aw_time + timedelta(hours=2)
                aw_formatted_datetime = aw_updated_time.strftime("%H:%M")
                area_weight_time.append(aw_formatted_datetime)


    if area_weight != [] and area_weight[-1] == 0:
        area_weight[-1] = area_weight[-2]
    if area_weight != [] and area_weight[0] == 0:
        area_weight[0] = area_weight[1]

    if area_weight == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            area_weight.append("NaN")

    if area_weight_time == []:
        time_now = datetime.now()
        area_weight_time = []

        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            time = time_now - timedelta(minutes=i)
            if aggregate_time[selected_time] == "1h":
                area_weight_time.append(time.strftime("%d-%m %H:%M"))
            else:
                area_weight_time.append(time.strftime("%H:%M"))

    area_weight = [x if x is not None else "NaN" for x in area_weight]


    ##################################### TENSILE MD ################################################

    for index, aggregation_fn in enumerate(aggregation_fns): # enumarate macht kein sinn !
        query_tables_tensile_md = f"""
        from(bucket: "AgentValues")
            |> range(start: {query_time_modified}, stop: now())
            |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
            |> filter(fn: (r) => r["_field"] == "TensileStrengthMD_avg")
            |> filter(fn: (r) => r["Unit"] == "N")
            |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
            |> yield(name: "last")
        """

        # Execute the Flux query and store the result in tables
        tables_tensile_force_md = query_api.query(query_tables_tensile_md, org=influxdb_config.org)
        tensile_force_md = []
  
        for table_tensile_force_md in tables_tensile_force_md:
            #print(table_tensile_force_md)
            for record_tensile_force_md in table_tensile_force_md.records:
                tf_md_value = record_tensile_force_md.values["_value"]
                tensile_force_md.append(tf_md_value)

    if tensile_force_md != [] and tensile_force_md[-1] == 0:
        tensile_force_md[-1] = tensile_force_md[-2]
    if tensile_force_md != [] and tensile_force_md[0] == 0:
        tensile_force_md[0] = tensile_force_md[1]

    if tensile_force_md == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            tensile_force_md.append("NaN")

    tensile_force_md = [x if x is not None else "NaN" for x in tensile_force_md]



    ##################################### TENSILE CD ################################################

    for index, aggregation_fn in enumerate(aggregation_fns):
        query_tables_tensile_cd = f"""
        from(bucket: "AgentValues")
            |> range(start: {query_time_modified}, stop: now())
            |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
            |> filter(fn: (r) => r["_field"] == "TensileStrengthCD_avg")
            |> filter(fn: (r) => r["Unit"] == "N")
            |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
            |> yield(name: "last")
        """

        # Execute the Flux query and store the result in tables
        tables_tensile_force_cd = query_api.query(query_tables_tensile_cd, org=influxdb_config.org)
        tensile_force_cd = []

        for table_tensile_force_cd in tables_tensile_force_cd:
            for record_tensile_force_cd in table_tensile_force_cd.records:
                tf_cd_value = record_tensile_force_cd.values["_value"]
                tensile_force_cd.append(tf_cd_value)

    if tensile_force_cd != [] and tensile_force_cd[-1] == 0:
        tensile_force_cd[-1] = tensile_force_cd[-2]
    if tensile_force_cd != [] and tensile_force_cd[0] == 0:
        tensile_force_cd[0] = tensile_force_cd[1]

    if tensile_force_cd == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            tensile_force_cd.append("NaN")

    tensile_force_cd = [x if x is not None else "NaN" for x in tensile_force_cd]


        #tensile_force_cd_all.append(tensile_force_cd)

    return [area_weight, tensile_force_md, tensile_force_cd], area_weight_time


############################################################################################################

### Humidty Ennvironment ###
def get_tear_length(selected_time, influxdb_config, query_api):

    query_time_modified = f"-{selected_time}"

    query_tear_length_md = f"""from(bucket: "LabValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "TearLength_MD1" or r["_field"] == "TearLength_MD2" or r["_field"] == "TearLength_MD3" or r["_field"] == "TearLength_MD4" or r["_field"] == "TearLength_MD5")
        |> filter(fn: (r) => r["Unit"] == "%")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: mean)
        |> yield(name: "mean")
    """

    # Execute the Flux query and store the result in tables
    tables_tear_length_md = query_api.query(query_tear_length_md, org=influxdb_config.org)
    tear_length_md = []
    tear_length_time = []

    print("hi")

    for table_tear_length_md in tables_tear_length_md:
        for record_tear_length_md in table_tear_length_md.records:
            tl_md_value = record_tear_length_md.values["_value"]
            tl_time = record_tear_length_md.values["_time"]

            tear_length_md.append(tl_md_value)

            tl_time_updated = tl_time + timedelta(hours=2)
            if aggregate_time[selected_time] == "1h":
                tl_formatted_datetime = tl_time_updated.strftime("%d-%m %H:%M")
            else:
                tl_formatted_datetime = tl_time_updated.strftime("%H:%M")
            tear_length_time.append(tl_formatted_datetime)

    if tear_length_md != [] and tear_length_md[-1] == 0:
        tear_length_md[-1] = tear_length_md[-2]
    if tear_length_md != [] and tear_length_md[0] == 0:
        tear_length_md[0] = tear_length_md[1]

    if tear_length_md == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            tear_length_md.append("NaN")

    if tear_length_time == []:
        time_now = datetime.now()
        tear_length_time = []

        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            time = time_now - timedelta(minutes=i)
            if aggregate_time[selected_time] == "1h":
                tear_length_time.append(time.strftime("%d-%m %H:%M"))
            else:
                tear_length_time.append(time.strftime("%H:%M"))
    
    tear_length_md = [x if x is not None else "NaN" for x in tear_length_md]


    ################### CD #########################################

    query_tensile_strength = f"""from(bucket: "LabValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "TearLength_CD1" or r["_field"] == "TearLength_CD2" or r["_field"] == "TearLength_CD3" or r["_field"] == "TearLength_CD4" or r["_field"] == "TearLength_CD5")
        |> filter(fn: (r) => r["Unit"] == "%")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: mean)
        |> yield(name: "mean")
        """

    # Execute the Flux query and store the result in tables
    tables_tear_length_cd = query_api.query(query_tensile_strength, org=influxdb_config.org)
    tear_length_cd = []

    for table_tear_length_cd in tables_tear_length_cd:
        for record_tensile_strength_cd in table_tear_length_cd.records:
            tl_cd_value = record_tensile_strength_cd.values["_value"]

            tear_length_cd.append(tl_cd_value)

    if tear_length_cd != [] and tear_length_cd[-1] == 0:
        tear_length_cd[-1] = tear_length_cd[-2]
    if tear_length_cd != [] and tear_length_cd[0] == 0:
        tear_length_cd[0] = tear_length_cd[1]


    if tear_length_cd == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            tear_length_cd.append("NaN")

    tear_length_cd = [x if x is not None else "NaN" for x in tear_length_cd]


    return [tear_length_md, tear_length_cd], tear_length_time


############################################################################################################

### Economics ###
def get_economics(selected_time, influxdb_config, query_api):
    query_time_modified = f"-{selected_time}"

    # Material Costs
    query_material_costs = f"""from(bucket: "AgentValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "CardDeliveryWeightPerArea" or r["_field"] == "CardDeliverySpeed")
        |> filter(fn: (r) => r["Unit"] == "g/m^2" or r["Unit"] == "m/min")
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
        |> yield(name: "last")"""

    tables_material_costs= query_api.query(query_material_costs, org=influxdb_config.org)
    card_delivery_weight_per_area = []
    card_delivery_speed = []


    for table_material_costs in tables_material_costs:

        print(tables_material_costs)
        for record_material_costs in table_material_costs.records:
            mc_value = record_material_costs.values["_value"]
            mc_field = record_material_costs.values["_field"]


            if mc_value == None: 
                mc_value = 0.0
   
            if mc_field == "CardDeliveryWeightPerArea":
                card_delivery_weight_per_area.append(mc_value)
            elif mc_field == "CardDeliverySpeed":
                card_delivery_speed.append(mc_value)


                

    print("cardD: ", len(card_delivery_speed))
    print("card: ", len(card_delivery_weight_per_area))


    if card_delivery_speed != [] and card_delivery_speed[-1] == 0:
        card_delivery_speed[-1] = card_delivery_speed[-2]
    if card_delivery_speed != [] and card_delivery_speed[0] == 0:
        card_delivery_speed[0] = card_delivery_speed[1]


    if len(card_delivery_weight_per_area) != len(card_delivery_speed):
        print("Length of lists are not the same")
    else:
        material_costs = [x * y * 6/100 * fibre_costs for x, y in zip(card_delivery_weight_per_area, card_delivery_speed)]

    if material_costs == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            material_costs.append(0)


    ###
    # Energy Costs 
    query_energy_costs = f"""from(bucket: "AgentValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "LinePowerConsumption")
        |> filter(fn: (r) => r["Unit"] == "kW")
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
        |> yield(name: "last")"""

    tables_energy_costs = query_api.query(query_energy_costs, org=influxdb_config.org)

    energy_costs = []
    energy_costs_time = []

    for table_energy_costs in tables_energy_costs:
        for record_energy_costs in table_energy_costs.records:
            pc_value = record_energy_costs.values["_value"]
            pc_time = record_energy_costs.values["_time"]
            if pc_value == None: 
                ec_value = 0.0
            else: 
                ec_value = pc_value * 0.28
            energy_costs.append(ec_value)
            pc_time_updated = pc_time + timedelta(hours=2)
            if aggregate_time[selected_time] == "1h":
                pc_formatted_datetime = pc_time_updated.strftime("%d-%m %H:%M")
            else:
                pc_formatted_datetime = pc_time_updated.strftime("%H:%M")
            energy_costs_time.append(pc_formatted_datetime)

    #########################################
    print("energy: ", len(energy_costs_time))


    if energy_costs != [] and energy_costs[-1] == 0:
        energy_costs[-1] = energy_costs[-2]
    if energy_costs != [] and energy_costs[0] == 0:
        energy_costs[0] = energy_costs[1]

    if energy_costs == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            energy_costs.append(0)

    if energy_costs_time == []:
        time_now = datetime.now()
        energy_costs_time = []

        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            time = time_now - timedelta(minutes=i)
            if aggregate_time[selected_time] == "1h":
                energy_costs_time.append(time.strftime("%d-%m %H:%M"))
            else:
                energy_costs_time.append(time.strftime("%H:%M"))

    ###
    # Production income
    query_production_income = f"""from(bucket: "AgentValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "ProductWidth" or r["_field"] == "ProductionSpeed")
        |> filter(fn: (r) => r["Unit"] == "m" or r["Unit"] == "m/min")
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
        |> yield(name: "last")"""

    tables_production_income = query_api.query(query_production_income, org=influxdb_config.org)
    production_width = []
    production_speed = []
    production_income = []

    for table_production_income in tables_production_income:
        for record_production_income in table_production_income.records:
            pi_value = record_production_income.values["_value"]
            pi_field = record_production_income.values["_field"]

            if pi_value == None: 
                pi_value = 0

            if pi_field == "ProductWidth":
                production_width.append(pi_value)
            elif pi_field == "ProductionSpeed":
                production_speed.append(pi_value)

    print("production_width: ", len(production_width))
    print("production_speed: ", len(production_speed))

    
    #print(len(production_width), len(production_speed))
    if len(production_width) != len(production_speed):
        print("Length of lists are not the same")
    else:
        production_income = [x * y * 60 * selling_price for x, y in zip(production_width, production_speed)]

        if production_income != [] and production_income[-1] == 0:
            production_income[-1] = production_income[-2]
        if production_income != [] and production_income[0] == 0:
            production_income[0] = production_income[1]


    if production_income == []:
        for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
            production_income.append(0)
    #print(production_income)


    ###
    #Contribution Margin 
    contribution_margin = [income - energy - material for income, energy, material in zip(production_income, energy_costs, material_costs)]
    #print(len(material_costs))
    return [energy_costs, material_costs, contribution_margin, production_income], energy_costs_time

############################################################################################################

### Line Power Consumption ### Economics ###
def get_line_power_consumption(chart, selected_time, influxdb_config, query_api):

    query_time_modified = f"-{selected_time}"

    query_energy_costs = f"""from(bucket: "AgentValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "LinePowerConsumption")
        |> filter(fn: (r) => r["Unit"] == "kW")
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
        |> yield(name: "last")"""

    tables_energy_costs = query_api.query(query_energy_costs, org=influxdb_config.org)
    line_power_consumption = []
    line_power_consumption_time = []

    for table_energy_costs in tables_energy_costs:
        for record_energy_costs in table_energy_costs.records:
            pc_value = record_energy_costs.values["_value"]
            pc_time = record_energy_costs.values["_time"]
            if pc_value == None: 
                pc_value = 0.0
            line_power_consumption.append(pc_value)
            pc_time_updated = pc_time + timedelta(hours=2)
            if aggregate_time[selected_time] == "1h":
                pc_formatted_datetime = pc_time_updated.strftime("%d-%m %H:%M")
            else:
                pc_formatted_datetime = pc_time_updated.strftime("%H:%M")
            line_power_consumption_time.append(pc_formatted_datetime)

    if line_power_consumption != [] and line_power_consumption[-1] == 0:
        line_power_consumption[-1] = line_power_consumption[-2]
    if line_power_consumption != [] and line_power_consumption[0] == 0:
        line_power_consumption[0] = line_power_consumption[1]


    if chart == "LinePowerConsumption":
        if line_power_consumption == []:
            for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
                line_power_consumption.append(0)


        if line_power_consumption_time == []:
            time_now = datetime.now()
            line_power_consumption_time = []

            for i in range(time_select_empty_table[selected_time] * 60, -1, -1):
                time = time_now - timedelta(minutes=i)
                if aggregate_time[selected_time] == "1h":
                    line_power_consumption_time.append(time.strftime("%d-%m %H:%M"))
                else:
                    line_power_consumption_time.append(time.strftime("%H:%M"))

        return line_power_consumption, line_power_consumption_time





############################################################################################################

# Handle time selection via Axios\Ajax
def handle_time_range(request):
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org) 
    query_api = client_influxdb.query_api()

    if request.method == "GET":
        selected_time = request.GET.get("timeRange")
        selected_header = request.GET.get("header")

        if selected_header == "NonwovenUnevennes": 
            query_data, query_time = get_nonwoven_unevenness("NonwovenUnevennes",selected_time, influxdb_config, query_api)
        elif selected_header == "CardFloorEvenness":
            query_data, query_time = get_nonwoven_unevenness("CardFloorEvenness", selected_time, influxdb_config, query_api)
        elif selected_header == "AmbientTemperature":
            query_data, query_time = get_ambient_temperature(selected_time, influxdb_config, query_api)
        elif selected_header == "LaboratoryValues":
            query_data, query_time = get_laboratory_values(selected_time, influxdb_config, query_api)
        elif selected_header == "TearLength":
            query_data, query_time = get_tear_length(selected_time, influxdb_config, query_api)
        elif selected_header == "Economics":
            query_data, query_time = get_economics(selected_time, influxdb_config, query_api)
        elif selected_header == "LinePowerConsumption":
            query_data, query_time = get_line_power_consumption("LinePowerConsumption", selected_time, influxdb_config, query_api)    


        return JsonResponse({"status": "success", 'timeRange': [query_data, query_time]})
    else:
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)


###########################################################################################################
# main function
def index(request):

    query_hours = request.GET.get('value')
    if query_hours == None:
        query_hours = '-1h'
    else:
        query_hours  = f"-{query_hours}h"

    get_hour = '1h'
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org) 
    query_api = client_influxdb.query_api()


    ### Nonwoven Uvenness ###
    nonwoven_uvenness, nonwoven_uvenness_time = get_nonwoven_unevenness("NonwovenUnevennes", get_hour, influxdb_config, query_api)
    
    ### Calculate Card Floor Eveness from NonwovenUnevenness ###
    card_floor_evenness, card_floor_evenness_time = get_nonwoven_unevenness("CardFloorEvenness", get_hour, influxdb_config, query_api)

    ### Ambient Temperatur ###
    ambient_temperature, ambient_temperature_time = get_ambient_temperature(get_hour, influxdb_config, query_api)

    ### Laboratory Values ###
    laboratory_values, laboratory_values_time = get_laboratory_values(get_hour, influxdb_config, query_api)

    ### Humidty Environment ###
    tear_length, tear_length_time = get_tear_length(get_hour, influxdb_config, query_api)

    ### Economics ###
    economics, economics_time = get_economics(get_hour, influxdb_config, query_api)

    ### Line Power Consumption ##
    line_power_consumption, line_power_consumption_time = get_line_power_consumption("LinePowerConsumption", get_hour, influxdb_config, query_api)


    context = {
        'nonwoven_uvenness': nonwoven_uvenness, 
        'nonwoven_uvenness_time': nonwoven_uvenness_time,
        'card_floor_evenness': card_floor_evenness,
        'card_floor_evenness_time': card_floor_evenness_time,
        'ambient_temperature': ambient_temperature[0],
        'humidity_environment': ambient_temperature[1],
        'ambient_temperature_time': ambient_temperature_time,
        'laboratory_values_time': laboratory_values_time,   
        'area_weight': laboratory_values[0], 
        'tensile_force_md': laboratory_values[1], 
        'tensile_force_cd': laboratory_values[2],
        'tear_length_md': tear_length[0],
        'tear_length_cd': tear_length[1],
        'tear_length_time': tear_length_time,
        'energy_costs_time': economics_time,
        'energy_costs': economics[0],
        'material_costs': economics[1],
        'production_income': economics[2],
        'contribution_margin': economics[3],
        'line_power_consumption': line_power_consumption, 
        'line_power_consumption_time': line_power_consumption_time
        }

    return render(request, 'Charts/performance.html', context)




# Function for updating nonwoven unevenness 
def update_nonwoven_unevenness_chart(request):
    updated_values_dict = {}

    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()

    ############################################################################################################

    ### Updating Nonwoven Unevenness ###
    query_performance = """from(bucket: "AgentValues")
    |> range(start: -1m, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "NonwovenUnevenness" and r["Iteration"] == "-1")
    |> filter(fn: (r) => r["Unit"] == "-")
    |> last()"""

    tables = query_api.query(query_performance, org=influxdb_config.org)

    if tables == []:
        now = datetime.now()
        now += timedelta(hours=2)
        updated_values_dict["NonwovenUnevennessTime"] = now
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                time = record.values["_time"]
                time += timedelta(hours=2)
                updated_values_dict["NonwovenUnevenness"] = value
                updated_values_dict["NonwovenUnevennessTime"] = time


    return JsonResponse(updated_values_dict, safe=False)


############################################################################################################

# function for updating card floor evenness
def update_card_floor_evenness_chart(request):
    updated_values_dict = {}

    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()

    query_performance = """from(bucket: "AgentValues")
    |> range(start: -1m, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "NonwovenUnevenness" and r["Iteration"] == "-1")
    |> filter(fn: (r) => r["Unit"] == "-")
    |> last()"""

    tables = query_api.query(query_performance, org=influxdb_config.org)

    if tables == []:
        now = datetime.now()
        now += timedelta(hours=2)
        updated_values_dict["CardFloorEvennessTime"] = now
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                time = record.values["_time"]
                time += timedelta(hours=2)
                updated_values_dict["NonwovenUnevenness"] = value
                updated_values_dict["CardFloorEvennessTime"] = time

                scaled_signal = (updated_values_dict["NonwovenUnevenness"] - unevenness_signal_mean) / unevenness_signal_std
                card_floor_evenness = scaled_signal * floor_quality_weight
                updated_values_dict["CardFloorEvenness"] = card_floor_evenness

    return JsonResponse(updated_values_dict, safe=False)


############################################################################################################

# function for updating ambient temperature
def update_ambient_temperature_chart(request):
    updated_values_dict = {}
  
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()

    ### Updating Ambient Temperature ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "AmbientTemperature" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["Unit"] == "°C")
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        now = datetime.now()
        now += timedelta(hours=2)
        updated_values_dict["AmbientTemperatureTime"] = now
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                time = record.values["_time"]
                time += timedelta(hours=2)
                updated_values_dict["AmbientTemperature"] = value
                updated_values_dict["AmbientTemperatureTime"] = time

    return JsonResponse(updated_values_dict, safe=False)


############################################################################################################

# function for updating laboratory values
def update_laboratory_values_chart(request):
    updated_values_dict = {}
  
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()

    ### Updating AreaWeight ###
    query_area = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "AreaWeightLane1" or r["_field"] == "AreaWeightLane2" or r["_field"] == "AreaWeightLane3")
        |> filter(fn: (r) => r["Unit"] == "g/m^2")
        |> last()
        |> mean(column: "_value")
    """
    
    tables = query_api.query(query_area, org=influxdb_config.org)
  
    if tables == []:
        now = datetime.now()
        now += timedelta(hours=2)
        updated_values_dict["AreaWeightTime"] = now
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                time = record.values["_time"]
                time += timedelta(hours=2)
                updated_values_dict["AreaWeight"] = value
                updated_values_dict["AreaWeightTime"] = time


    ### Tensile MD ###
    query_area_md = """
    from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "TensileStrengthMD_avg")
        |> filter(fn: (r) => r["Unit"] == "N")
        |> last()
    """

    tables = query_api.query(query_area_md, org=influxdb_config.org)
  
    if tables == []:
        pass
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values_dict["TensileMD"] = value


    ### Tensile CD ###
    query_area_cd = """
    from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "TensileStrengthCD_avg")
        |> filter(fn: (r) => r["Unit"] == "N")
        |> last()
    """

    tables = query_api.query(query_area_cd, org=influxdb_config.org)
  
    if tables == []:
        pass
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values_dict["TensileCD"] = value

    return JsonResponse(updated_values_dict, safe=False)


############################################################################################################

# function for updating humidty environment
def update_tear_length_chart(request):
    updated_values_dict = {}
  
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()

    query_tear_length_md = """from(bucket: "LabValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "TearLength_MD1" and r["_field"] == "TearLength_MD2" and r["_field"] == "TearLength_MD3" and r["_field"] == "TearLength_MD4" and r["_field"] == "TearLength_MD5")
        |> filter(fn: (r) => r["Unit"] == "%")
        |> last()
        |> mean(column: "_value")
    """

    tables = query_api.query(query_tear_length_md, org=influxdb_config.org)

    if tables == []:
        now = datetime.now()
        now += timedelta(hours=2)
        updated_values_dict["TearLengthTime"] = now
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                time = record.values["_time"]
                time += timedelta(hours=2)
                updated_values_dict["TearLengthMD"] = value
                updated_values_dict["TearLengthTime"] = time


    ########################################################################

    query_tear_length_cd = """from(bucket: "LabValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "LabValues")
        |> filter(fn: (r) => r["_field"] == "TearLength_MD1" and r["_field"] == "TearLength_MD2" and r["_field"] == "TearLength_MD3" and r["_field"] == "TearLength_MD4" and r["_field"] == "TearLength_MD5")
        |> filter(fn: (r) => r["Unit"] == "%")
        |> last()
        |> mean(column: "_value")
    """

    tables = query_api.query(query_tear_length_cd, org=influxdb_config.org)

    if tables == []:
        pass
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values_dict["TearLengthCD"] = value
 

    return JsonResponse(updated_values_dict, safe=False)


############################################################################################################

# function for updating economics
def update_economics_chart(request):
    updated_values_dict = {}
  
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()

    ### Updating Energy Costs ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "LinePowerConsumption" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["Unit"] == "kW")
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values_dict["EnergyCosts"] = 0.0
        now = datetime.now()
        now += timedelta(hours=2)
        updated_values_dict["EconomicsTime"] = now
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                time = record.values["_time"]
                time += timedelta(hours=2)
                ec_value = value * 0.28
                updated_values_dict["EnergyCosts"] = ec_value
                updated_values_dict["EconomicsTime"] = time


    ### updating material costs
    query_material_costs = f"""from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "CardDeliveryWeightPerArea" or r["_field"] == "CardDeliverySpeed")
        |> filter(fn: (r) => r["Unit"] == "g/m^2" or r["Unit"] == "m/min")
        |> last()"""

    tables_material_costs= query_api.query(query_material_costs, org=influxdb_config.org)

    if tables_material_costs == []:
        updated_values_dict["MaterialCosts"] = 0.0

    else:
        for table_material_costs in tables_material_costs:
            for record_material_costs in table_material_costs.records:
                mc_value = record_material_costs.values["_value"]
                mc_field = record_material_costs.values["_field"]

                if mc_value == None: 
                    mc_value = 0.0

                if mc_field == "CardDeliveryWeightPerArea":
                    card_delivery_weight_per_area = mc_value
                elif mc_field == "CardDeliverySpeed":
                    card_delivery_speed = mc_value

        updated_values_dict["MaterialCosts"]  = card_delivery_speed * card_delivery_weight_per_area * 6/100 * fibre_costs



    ### Updating Production income ###
    query_production_income = f"""from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "ProductWidth" or r["_field"] == "ProductionSpeed")
        |> filter(fn: (r) => r["Unit"] == "m" or r["Unit"] == "m/min")
        |> last()"""

    tables_production_income = query_api.query(query_production_income, org=influxdb_config.org)

    if tables_production_income == []:
        updated_values_dict["ProductionIncome"] = 0.0
    else:
        for table_production_income in tables_production_income:
            for record_production_income in table_production_income.records:
                pi_value = record_production_income.values["_value"]
                pi_field = record_production_income.values["_field"]

                if pi_value == None: 
                    pi_value = 0

                if pi_field == "ProductWidth":
                    production_width = pi_value
                elif pi_field == "ProductionSpeed":
                    production_speed = pi_value

        updated_values_dict["ProductionIncome"] = production_width * production_speed * 60 * 2.10 


    updated_values_dict["ContributionMargin"] = updated_values_dict["ProductionIncome"] - updated_values_dict["EnergyCosts"] - updated_values_dict["MaterialCosts"] 
    
    return JsonResponse(updated_values_dict, safe=False)
 

############################################################################################################

# function for line power consumption
def update_line_power_consumption_chart(request):
    updated_values_dict = {}
  
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()

    ### Updating Energy Costs and Line Power Consumption ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "LinePowerConsumption" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["Unit"] == "kW")
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values_dict["LinePowerConsumption"] = 0.0
        now = datetime.now()
        now += timedelta(hours=2)
        updated_values_dict["LinePowerConsumptionTime"] = now

    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                time = record.values["_time"]
                time += timedelta(hours=2)
                updated_values_dict["LinePowerConsumption"] = value
                updated_values_dict["LinePowerConsumptionTime"] = time

        
    return JsonResponse(updated_values_dict, safe=False)