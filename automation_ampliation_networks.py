#######################################################################################
# Automação de Projeto de Ampliação de Capacidade de Sistemas de Comunicações Ópticas
#
# Autor: Higor Antonio de Brito Moreira
#
#######################################################################################


import re
import pandas as pd

##########################################
#Funções
##########################################

def compare_gsnr(bands, transponders):
    compare = {}
    for band, transponder_list in bands.items():
        compare[band] = []
        print(f"Comparação na banda {band}:")
        for transponder_info in transponder_list:
            transponder_id = transponder_info['Transponder']
            gsnr = transponder_info['GSNR']
            channel = transponder_info['Canal']
            #Verificar se o transponder existe no dicionário de requisitos
            if transponder_id in transponders:
                gsnr_req = transponders[transponder_id]['GSNRreq']
                modulation = transponders[transponder_id]['Modulation_Type']
                data_rate = transponders[transponder_id]['Data_Rate']
                capacity_band = int(data_rate)*int(channel)
                #Comparação dos valores e adicionar os que atendem ao dicionário de comparação
                if gsnr >= gsnr_req:
                    resultado = "Atende"
                    compare[band].append({
                        "Transponder": transponder_id,
                        "GSNR": gsnr,
                        "GSNRreq": gsnr_req,
                        "Modulation_Type": modulation,
                        "Data_Rate": data_rate,
                        "Canal": channel,
                        "Capacidade": capacity_band
                    })
                    #Exibir o resultado das comparações
                    print(f"  {transponder_id} - Channel:{channel} - GSNR:{gsnr} -> {resultado}")
                else:
                    resultado = "Não Atende"

            #Remover a chave da banda se nenhum transponder nela atender aos requisitos.
            if not compare[band]:
                del compare[band]
    return compare

#Calculando o Custo por Cenário e por Banda de Cenário.

def total_cost_calculate(scenarios, equipment_cost):
    total_cost_final = {}
    
    for scenario, devices in scenarios.items():
        total_cost = 0
        band_costs = {}
        for device, bands in devices.items():
            if device in equipment_cost:
                #Usando a banda em uma lista
                band_list = list(bands.items())
                for idx, (band, quantidade) in enumerate(band_list):
                    band_cost = quantidade * equipment_cost[device].get(band, 0)
                    total_cost += band_cost

                    #Armazenando o custo por banda
                    if band in band_costs:
                        band_costs[band] += band_cost
                    else:
                        band_costs[band] = band_cost

                    #Identifica a segunda banda, onde será somado o valor de Fibra e a armazena.
                    if idx == 1:  #A segunda banda é o índice 1
                        second_band = band

        #Adiciona o valor da fibra à segunda banda, se a fibra estiver presente
        if "Fiber" in band_costs and second_band:
            band_costs[second_band] += band_costs["Fiber"]
            del band_costs["Fiber"]  #Remove a fibra após adicionar ao segundo item

        #Adiciona o custo total do cenário e o custo por banda ao resultado final
        total_cost_final[scenario] = {
            "Total Cost": total_cost,
            "Band Cost": band_costs
        }
    #Retorna o dicionário
    return total_cost_final

#Unir dicionários

def merge_dicts(d1, d2):
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            # Mescla os sub-dicionários recursivamente
            d1[key] = merge_dicts(d1[key], value)
        else:
            # Sobrescreve ou adiciona o valor
            d1[key] = value
    return d1

#Função que verifica dominância nos cenários:

def dominates(scenario1, scenario2):
    #Retorna True se scenario1 domina scenario2.
    cost1, bit1 = scenario1['Total Cost'], scenario1['BIT']
    cost2, bit2 = scenario2['Total Cost'], scenario2['BIT']
    return (cost1 <= cost2 and bit1 <= bit2) and (cost1 < cost2 or bit1 < bit2)

#Função que conta quantas vezes um cenário é dominado

def count_dominance(scenario_key, scenario_data, all_scenarios):
    return sum(
        1 for other_key, other_data in all_scenarios.items()
        if scenario_key != other_key and dominates(other_data, scenario_data)
    )

##########################################
#Iniciando
##########################################

#Distancia do Enlace em Estudo
dist_enlace = 837

#Dicionário com os dados dos Transponders
transponders_base = {
    "TR1": {"GSNRreq": 9.8, "Modulation_Type": "PM-QPSK", "Data_Rate":"100"},
    "TR2": {"GSNRreq": 16.55, "Modulation_Type": "PM-16QAM", "Data_Rate":"200"},
    "TR3": {"GSNRreq": 16.55, "Modulation_Type": "PM-16QAM", "Data_Rate":"400"},
    "TR4": {"GSNRreq": 22.5, "Modulation_Type": "PM-64QAM", "Data_Rate":"400"},
    "TR5": {"GSNRreq": 16.55, "Modulation_Type": "PM-16QAM", "Data_Rate":"800"},
    "TR6": {"GSNRreq": 19.5, "Modulation_Type": "PM-32QAM", "Data_Rate":"800"},
    "TR7": {"GSNRreq": 22.5, "Modulation_Type": "PM-64QAM", "Data_Rate":"800"}
}

#Lista de Custo por Equipamento
equipment_cost_per_scenario = {
    "Amplifier": {"C": 1, "C1": 1 , "L": 1.2, "S1": 1.8, "S2": 1.8},
    "Mux/Demux": {"C": 0.4, "C1": 0.4, "L": 0.4, "S1": 0.4, "S2": 0.4},
    "WSS": {"C": 5, "C1": 5, "L": 6, "S1": 9, "S2": 9},
    "Transponder": {"C": 36, "C1": 36, "L": 43.2, "S1": 64.8, "S2": 64.8},
    "Average": {"Fiber": 0.5}
}

scenario = {
    "A": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 6,"L": 8}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 240, "L": 288}, "Average": {"Fiber": 0}},
    "B": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 6,"L": 8}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 240, "L": 320}, "Average": {"Fiber": 0}},
    "C": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 6,"L": 4}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 240, "L": 160}, "Average": {"Fiber": 0}},
    "D": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 4,"L": 8}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 126, "L": 300}, "Average": {"Fiber": 0}},
    "E": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 4,"L": 4}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 126, "L": 160}, "Average": {"Fiber": 0}},
    "F": {"Amplifier": {"C": 0, "S1": 13}, "Mux/Demux": {"C": 8,"S1": 8}, "WSS": {"C": 2,"S1": 2}, "Transponder": {"C": 252, "S1": 296}, "Average": {"Fiber": 0}},
    "G": {"Amplifier": {"C": 0, "S2": 13}, "Mux/Demux": {"C": 6,"S2": 8}, "WSS": {"C": 2,"S2": 2}, "Transponder": {"C": 240, "S2": 320}, "Average": {"Fiber": 0}},
    "H": {"Amplifier": {"C": 0, "S1": 13}, "Mux/Demux": {"C": 4,"S1": 8}, "WSS": {"C": 2,"S1": 2}, "Transponder": {"C": 126, "S1": 296}, "Average": {"Fiber": 0}},
    "I": {"Amplifier": {"C": 0, "S2": 13}, "Mux/Demux": {"C": 4,"S2": 8}, "WSS": {"C": 2,"S2": 2}, "Transponder": {"C": 126, "S2": 296}, "Average": {"Fiber": 0}},
    "JF": {"Amplifier": {"C":0,"C1": 13}, "Mux/Demux": {"C":6,"C1": 4}, "WSS": {"C":2,"C1": 2}, "Transponder": {"C":240,"C1": 160}, "Average": {"Fiber": dist_enlace}},
    "KF": {"Amplifier": {"C":0,"C1": 13}, "Mux/Demux": {"C":4,"C1": 2}, "WSS": {"C":2,"C1": 2}, "Transponder": {"C": 126,"C1": 74}, "Average": {"Fiber": dist_enlace}},
    "LF": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 6,"L": 4}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 240, "L":160}, "Average": {"Fiber": dist_enlace}},
    "MF": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 4,"L": 8}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 126, "L":300}, "Average": {"Fiber": dist_enlace}},
    "NF": {"Amplifier": {"C": 0, "L": 13}, "Mux/Demux": {"C": 4,"L": 4}, "WSS": {"C": 2,"L": 2}, "Transponder": {"C": 126, "L":160}, "Average": {"Fiber": dist_enlace}},
    "OF": {"Amplifier": {"C": 0, "S1": 13}, "Mux/Demux": {"C": 4,"S1": 8}, "WSS": {"C": 2,"S1": 2}, "Transponder": {"C": 126, "S1":296}, "Average": {"Fiber": dist_enlace}},
    "PF": {"Amplifier": {"C": 0, "S2": 13}, "Mux/Demux": {"C": 4,"S2": 8}, "WSS": {"C": 2,"S2": 2}, "Transponder": {"C": 126, "S2":296}, "Average": {"Fiber": dist_enlace}},    
    }

scenario_bit = {
    "A": {"C": 12000000000000, "L": 28800000000000, "Fiber": 1},
    "B": {"C": 24000000000000, "L": 16000000000000, "Fiber": 1},
    "C": {"C": 24000000000000, "L": 16000000000000, "Fiber": 1},
    "D": {"C": 25200000000000, "L": 15000000000000, "Fiber": 1},
    "E": {"C": 25200000000000, "L": 16000000000000, "Fiber": 1},
    "F": {"C": 25200000000000, "S1": 14800000000000, "Fiber": 1},
    "G": {"C": 24000000000000, "S2": 16000000000000, "Fiber": 1},
    "H": {"C": 25200000000000, "S1": 14800000000000, "Fiber": 1},
    "I": {"C": 25200000000000, "S2": 14800000000000, "Fiber": 1},
    "JF": {"C": 24000000000000, "C1": 16000000000000, "Fiber": 1}, 
    "KF": {"C": 25200000000000, "C1": 14800000000000, "Fiber": 1},
    "LF": {"C": 24000000000000, "L": 16000000000000,"Fiber": 1},
    "MF": {"C": 25200000000000, "L": 15000000000000, "Fiber": 1},
    "NF": {"C": 25200000000000, "L": 16000000000000, "Fiber": 1},
    "OF": {"C": 25200000000000, "S1": 14800000000000, "Fiber": 1},
    "PF": {"C": 25200000000000, "S2": 14800000000000, "Fiber": 1}
}

#Lista de arquivos de entrada
files = [
    "/home/comptel/users/higor/resultados/bandC.txt",
    "/home/comptel/users/higor/resultados/bandL.txt",
    "/home/comptel/users/higor/resultados/bandS1.txt",
    "/home/comptel/users/higor/resultados/bandS2.txt"
]

#Dicionário para armazenar os resultados dos transponders por banda
resultados = {}

#Extrair os dados dos arquivos
for file in files:
    #Extrai o nome da banda do nome do arquivo
    band = re.search(r"band([A-Z0-9]{1,2})", file).group(1)
    
    #Faz a leitura do arquivo inteiro como um DataFrame
    with open(file, 'r') as f:
        lines = f.readlines()

    #Lista declarada para armazenar os dados das linhas que correspondem aos padrões de valores
    data = []
    canal = []
    #Processa as linhas do arquivo
    for line in lines:

        #Verifica se a linha contém os dados desejados e extrai os valores
        if re.match(r"^\s*(\d+)\s+(\d+\.\d+.*)\s+(-?\d+\.\d{2})\s+([\d\-\.]+)\s+([\d\-\.]+)\s+([\d\-\.]+)\s*$", line):
            #Dividimos a linha em partes com múltiplos espaços
            values = re.split(r'\s+', line.strip())
            data.append(values)

    #Cria o DataFrame com os dados extraídos
    if data:
        df = pd.DataFrame(data, columns=['Channel', 'Channel Frequency', 'Channel Power', 'OSNR ASE', 'SNR NLI', 'GSNR'])
        #Transforma os valores em númerico
        df['GSNR'] = pd.to_numeric(df['GSNR'])
        df['Channel'] = pd.to_numeric(df['Channel'])
        
        #Define a separação dos canais dos transponders
        df['Group'] = (df['Channel'] == 1).cumsum()
        
        #Calcula a média do GSNR por transponder e indica o número de canais
        average_per_group = df.groupby('Group')['GSNR'].mean().reset_index()
        last_channel_per_group = df.groupby('Group')['Channel'].last().reset_index()
        combine_per_group = average_per_group.merge(last_channel_per_group, on='Group', suffixes=('', '_Ultimo'))

        #Cria um dicionário para armazenar os resultados do GSNR dos transponders
        transponders = {}
        for i, grupo in combine_per_group.iterrows():
            if band not in resultados:
                resultados[band] = []
            transponder_name = f"TR{int(grupo['Group'])}"
            transponder_gsnr = round(grupo['GSNR'], 2)
            channel_transponder = int(grupo['Channel'])
            resultados[band].append({'Transponder': transponder_name, 'GSNR': transponder_gsnr, 'Canal': channel_transponder})
        
#Dicionário com os TRs que atendem aos requisitos
print("###########################################################################################################################################################\n")
print("Transponders Disponíveis:")
print("\n")
comparison = compare_gsnr(resultados, transponders_base)
print("\n###########################################################################################################################################################\n")
print("Calculando os Custos Relativos por Cenário:")
print("\n")

result = total_cost_calculate(scenario, equipment_cost_per_scenario)

#Mostrando o Custo Relativo e Armazenando o mesmo em outro dicionário
total_relative = {}
for scene, cost in result.items():
    total = cost["Total Cost"]
    total_relative[scene] = {
            "Total Cost": total,
        }
    print(f"Cenário - {scene}: Custo Total Relativo do Cenário = {total:.2f}")

print("\n###########################################################################################################################################################\n")
print("Calculando os Custos Relativos por Bit Rate:")
print("\n")

#Mostrando o Custo Relativo por bit e Armazenando o mesmo em outro dicionário
total_relative_bit = {}
total_bit = 0 
for scene, cost in result.items():
    total_bit_scenario = 0
    for scene_band, value in cost["Band Cost"].items():  
        if scene_band != "Fiber":  
            total_bit_band = value / scenario_bit[scene].get(scene_band, 0)
            total_bit_scenario += total_bit_band
    total_relative_bit[scene] = {
            "BIT": total_bit_scenario,
        }
    print(f"Cenário {scene} - Bit: {total_bit_scenario}")

print("\n###########################################################################################################################################################\n")

combine = merge_dicts(total_relative, total_relative_bit)

#Criar uma lista com a contagem de dominancia dos cenários e mostrar os cenários de menor dominancia para a maior:

dominance_counts = [
    (key, data, count_dominance(key, data, combine))
    for key, data in combine.items()
]

sorted_scenarios = sorted(dominance_counts, key=lambda x: x[2])

ranked_scenarios = [
    {"Scenario": key, "Total Cost": data["Total Cost"], "BIT": data["BIT"], "Dominance Count": count}
    for key, data, count in sorted_scenarios
]

print("Cenários Ordenados por Dominância - Melhor ao Pior Cenário:\n")
for scenario in ranked_scenarios:
    print(f"Cenário: {scenario['Scenario']}, "
          f"Dominance Count: {scenario['Dominance Count']}")

print("\n###########################################################################################################################################################\n") 

#Percorre todos os cenários e verifica quais não são dominados por nenhum outro, retornando os cenários mais vantajosos considerando o critério de dominância.

pareto_front = []
for scenario_key, scenario_data in combine.items():
    is_dominated = False
    for other_key, other_data in combine.items():
        if scenario_key != other_key and dominates(other_data, scenario_data):
            is_dominated = True
            break
    if not is_dominated:
        pareto_front.append((scenario_key, scenario_data))

#Mostrando o cenário na Fronteira de Pareto

print("Cenários na fronteira de Pareto:\n")
for scenario, data in pareto_front:
    print(f"O melhor cenário é o {scenario}: Total Cost = {data['Total Cost']}, BIT = {data['BIT']}")

print("\n###########################################################################################################################################################\n")