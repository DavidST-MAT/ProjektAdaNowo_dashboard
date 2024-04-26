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

aggregate_time = {
    '1h': '1m',
    '3h': '1m',
    '6h': '1m',
    '12h': '1m',
    '30d': '1h'
}



# Influx Configuration
class InfluxDBConfig:

    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        #self.token = os.getenv("INFLUXDB_TOKEN", "Qc6s7RKI7ZnQpB5ZdesJzEmgd46XLGRmcXv5RJRbhTUc758Ma8g-LQv6_A2p125BZohkhbYnEhVtpeOHJ-BqTw==")
        self.token = os.getenv("INFLUXDB_TOKEN", "L43SXxiyt-jYReLa0NdsUgvIvCSk_BsC7shKlf2HXiboELJsVYbWEQfv57-Ml0GX58m1CjateBgEBwFKEtK4mQ==")
        self.org = os.getenv("INFLUXDB_ORG", "MAT")


############################################################################################################

### NonwovenUnevenness ###
def get_nonwoven_unevenness(selected_time, influxdb_config, query_api):

    query_time_modified = f"-{selected_time}"

    query_nonwoven_uvenness = f"""from(bucket: "AgentValues")
        |> range(start: {query_time_modified}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "NonwovenUnevenness")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: {aggregate_time[selected_time]}, fn: last)
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
                nu_value = 0.0
            nonwoven_uvenness.append(nu_value)
            nu_time_updated = nu_time + timedelta(hours=2)
            if aggregate_time[selected_time] == "1h":
                nu_formatted_datetime = nu_time_updated.strftime("%Y-%m-%d")
            else:
                nu_formatted_datetime = nu_time_updated.strftime("%H:%M:%S")
            nonwoven_uvenness_time.append(nu_formatted_datetime)
            print(nu_time)


    if nonwoven_uvenness != [] and nonwoven_uvenness[-1] == 0:
        nonwoven_uvenness[-1] = nonwoven_uvenness[-2]
    if nonwoven_uvenness != [] and nonwoven_uvenness[0] == 0:
        nonwoven_uvenness[0] = nonwoven_uvenness[1]

    return nonwoven_uvenness, nonwoven_uvenness_time





def handle_time_range(request):
    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org) 
    query_api = client_influxdb.query_api()

    if request.method == "GET":
        selected_time = request.GET.get("timeRange")
        query_data, query_time = get_nonwoven_unevenness(selected_time, influxdb_config, query_api)

        return JsonResponse({"status": "success", 'timeRange': [query_data, query_time]})
    else:
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)



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
    nonwoven_uvenness, nonwoven_uvenness_time = get_nonwoven_unevenness(get_hour, influxdb_config, query_api)
    
    ### Calculate Card Floor Eveness from NonwovenUnevenness ###
    scaled_signal = [(x - unevenness_signal_mean) / unevenness_signal_std for x in nonwoven_uvenness]
    card_floor_evenness = [x * floor_quality_weight for x in scaled_signal]


    ############################################################################################################

    ### Ambient Temperatur ###
    query_ambient_temperature = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "AmbientTemperature")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    tables_ambient_temperature = query_api.query(query_ambient_temperature, org=influxdb_config.org)
    ambient_temperature = []
    ambient_temperature_time = []


    for table_ambient_temperature in tables_ambient_temperature:
        for record_ambient_temperature in table_ambient_temperature.records:
            at_value = record_ambient_temperature.values["_value"]
            at_time = record_ambient_temperature.values["_time"]
            if at_value == None: 
                at_value = 0.0
            ambient_temperature.append(at_value)
            at_time_updated = at_time + timedelta(hours=2)
            at_formatted_datetime = at_time_updated.strftime("%H:%M:%S")
            ambient_temperature_time.append(at_formatted_datetime)

    if ambient_temperature != [] and ambient_temperature[-1] == 0:
        ambient_temperature[-1] = ambient_temperature[-2]
    if ambient_temperature != [] and ambient_temperature[0] == 0:
        ambient_temperature[0] = ambient_temperature[1]

    
    ##############################################################################################################

    ### Laboratory Values ###
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
            #print(table_area_weight)
            for record_area_weight in table_area_weight.records:
                aw_value = record_area_weight.values["_value"]
                aw_time = record_area_weight.values["_time"]
                if aw_value == None: 
                    aw_value = 0
                area_weight.append(aw_value)
                aw_updated_time = aw_time + timedelta(hours=2)
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
            #print(table_tensile_force_md)
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
                he_value = 0.0
            humidity_environment.append(he_value)
            he_time_updated = he_time + timedelta(hours=2)
            he_formatted_datetime = he_time_updated.strftime("%H:%M:%S")
            humidity_environment_time.append(he_formatted_datetime)


    if humidity_environment != [] and humidity_environment[-1] == 0:
        humidity_environment[-1] = humidity_environment[-2]
    if humidity_environment != [] and humidity_environment[0] == 0:
        humidity_environment[0] = humidity_environment[1]


    ############################################################################################################

    ### Economics ###

    # Material Costs
    query_material_costs = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "CardDeliveryWeightPerArea" or r["_field"] == "CardDeliverySpeed")
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    tables_material_costs= query_api.query(query_material_costs, org=influxdb_config.org)
    card_delivery_weight_per_area = []
    card_delivery_speed = []

    for table_material_costs in tables_material_costs:
        for record_material_costs in table_material_costs.records:
            mc_value = record_material_costs.values["_value"]
            mc_field = record_material_costs.values["_field"]

            if mc_value == None: 
                mc_value = 0.0

            if mc_field == "CardDeliveryWeightPerArea":
                card_delivery_weight_per_area.append(mc_value)
            elif mc_field == "CardDeliverySpeed":
                card_delivery_speed.append(mc_value)

    if len(card_delivery_weight_per_area) != len(card_delivery_speed):
        print("Length of lists are not the same")
    else:
        material_costs = [x * y * 6/100 * fibre_costs for x, y in zip(card_delivery_weight_per_area, card_delivery_speed)]


    ###
    # Energy Costs and Line Power Consumption
    query_energy_costs = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "LinePowerConsumption")
        |> group(columns: ["_measurement"])
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    tables_energy_costs = query_api.query(query_energy_costs, org=influxdb_config.org)
    energy_costs = []
    line_power_consumption = []
    line_power_consumption_time = []

    for table_energy_costs in tables_energy_costs:
        for record_energy_costs in table_energy_costs.records:
            pc_value = record_energy_costs.values["_value"]
            pc_time = record_energy_costs.values["_time"]
            if pc_value == None: 
                pc_value = 0.0
                ec_value = 0.0
            else:
                ec_value= pc_value * 0.28
            line_power_consumption.append(pc_value)
            energy_costs.append(ec_value)
            pc_time_updated = pc_time + timedelta(hours=2)
            pc_formatted_datetime = pc_time_updated.strftime("%H:%M:%S")
            line_power_consumption_time.append(pc_formatted_datetime)

    if energy_costs != [] and energy_costs[-1] == 0:
        energy_costs[-1] = energy_costs[-2]
    if energy_costs != [] and energy_costs[0] == 0:
        energy_costs[0] = energy_costs[1]

    if line_power_consumption != [] and line_power_consumption[-1] == 0:
        line_power_consumption[-1] = line_power_consumption[-2]
    if line_power_consumption != [] and line_power_consumption[0] == 0:
        line_power_consumption[0] = line_power_consumption[1]


    ###
    # Production income
    query_production_income = f"""from(bucket: "AgentValues")
        |> range(start: {query_hours}, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "ProductWidth" or r["_field"] == "ProductionSpeed")
        |> aggregateWindow(every: 1m, fn: last)
        |> yield(name: "last")"""

    tables_production_income = query_api.query(query_production_income, org=influxdb_config.org)
    production_width = []
    production_speed = []

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

    if len(production_width) != len(production_speed):
        print("Length of lists are not the same")
    else:
        production_income = [x * y * 60 * selling_price for x, y in zip(production_width, production_speed)]

    if production_income != [] and production_income[-1] == 0:
        production_income[-1] = production_income[-2]


    ###
    #Contribution Margin 
    contribution_margin = [income - energy - material for income, energy, material in zip(production_income, energy_costs, material_costs)]


    ############################################################################################################

    context = {
        'nonwoven_uvenness': nonwoven_uvenness, 
        'nonwoven_uvenness_time': nonwoven_uvenness_time,
        'card_floor_evenness': card_floor_evenness,
        'ambient_temperature': ambient_temperature,
        'ambient_temperature_time': ambient_temperature_time,  
        'area_weights': area_weights, 
        'area_weight_time': area_weight_time, 
        'tensile_force_md_all': tensile_force_md_all, 
        'tensile_force_cd_all': tensile_force_cd_all,
        'humidity_environment': humidity_environment,
        'humidity_environment_time': humidity_environment_time,
        'material_costs': material_costs,
        'energy_costs': energy_costs,
        'line_power_consumption': line_power_consumption, 
        'line_power_consumption_time': line_power_consumption_time,
        'production_income': production_income,
        'contribution_margin': contribution_margin,
        }

    return render(request, 'Charts/performance.html', context)






# Function for updating the Charts 
def updateChartOneMinute(request):
    updated_values_dict = {}
    updated_values = []

    influxdb_config = InfluxDBConfig()
    client_influxdb = InfluxDBClient(url=influxdb_config.url, token=influxdb_config.token, org=influxdb_config.org)
    query_api = client_influxdb.query_api()


    ############################################################################################################

    ### Updating Nonwoven Unevenness ###
    query_performance = """from(bucket: "AgentValues")
    |> range(start: -1m, stop: now())
    |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "NonwovenUnevenness" and r["Iteration"] == "-1")
    |> group(columns: ["_field"])
    |> last()"""

    tables = query_api.query(query_performance, org=influxdb_config.org)

    if tables == []:
        updated_values_dict["NonwovenUnevenness"] = 0.0
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values_dict["NonwovenUnevenness"] = value


    ############################################################################################################

    ### Updating Card Floor Evenness ###
    scaled_signal= (updated_values_dict["NonwovenUnevenness"] - unevenness_signal_mean) / unevenness_signal_std
    card_floor_evenness = scaled_signal * floor_quality_weight
    updated_values_dict["CardFloorEvenness"] = card_floor_evenness


    ############################################################################################################

    ### Updating Ambient Temperature ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "AmbientTemperature" and r["Iteration"] == "-1")
        |> group(columns: ["_field"])
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values_dict["AmbientTemperature"] = 0.0
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values_dict["AmbientTemperature"] = value

    
    ###########################################################################################################

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


    ###########################################################################################################

    ### Updating Humidty Environment ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "RelativeHumidityEnvironment" and r["Iteration"] == "-1")
        |> group(columns: ["_field"])
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values_dict["RelativeHumidityEnvironment"] = 0.0
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                updated_values_dict["RelativeHumidityEnvironment"] = value


    ###########################################################################################################

    ### Updating Energy Costs and Line Power Consumption ###
    query_energy = """from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "QualityValues" and r["_field"] == "LinePowerConsumption" and r["Iteration"] == "-1")
        |> group(columns: ["_field"])
        |> last()"""

    tables = query_api.query(query_energy, org=influxdb_config.org)

    if tables == []:
        updated_values_dict["LinePowerConsumption"] = 0.0
        updated_values_dict["EnergyCosts"] = 0.0
    else:
        for table in tables:
            for record in table.records:
                value = record.values["_value"]
                ec_value = value * 0.28
                updated_values_dict["LinePowerConsumption"] = value
                updated_values_dict["EnergyCosts"] = ec_value


    
    ### Updating Production income ###
    query_production_income = f"""from(bucket: "AgentValues")
        |> range(start: -1m, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "ActualValues" and r["Iteration"] == "-1")
        |> filter(fn: (r) => r["_field"] == "ProductWidth" or r["_field"] == "ProductionSpeed")
        |> last()"""

    tables_production_income = query_api.query(query_production_income, org=influxdb_config.org)

    if tables_production_income == []:
        updated_values.append(0)
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

        production_income = production_width * production_speed * 60 * 2.10 
        updated_values.append(production_income)


    
    return JsonResponse(updated_values_dict, safe=False)





