import numpy as np
import pandas as pd
import cvxpy as cp
import gurobipy as gp

# ======================  参数设定 ======================  
N, R = 64, 9
N_s = 10
S = 14
lamda = 1600

subject_set = ["a1社区居委会","a1社区物业","a2社区居委会","a2社区物业","a3社区居委会","a3社区物业","b1社区居委会","b1社区物业","b2社区居委会","b2社区物业","b3社区居委会","b3社区物业","c1社区居委会","c1社区物业","c2社区居委会","c2社区物业","c3社区居委会","c3社区物业","d1社区居委会","d1社区物业","d2社区居委会","d2社区物业","d3社区居委会","d3社区物业","e1社区居委会","e1社区物业","e2社区居委会","e2社区物业","e3社区居委会","e3社区物业","f1社区居委会","f1社区物业","f2社区居委会","f2社区物业","f3社区居委会","f3社区物业","g1社区居委会","g1社区物业","g2社区居委会","g2社区物业","g3社区居委会","g3社区物业","h1社区居委会","h1社区物业","h2社区居委会","h2社区物业","h3社区居委会","h3社区物业","i1社区居委会","i1社区物业","i2社区居委会","i2社区物业","i3社区居委会","i3社区物业",
"A街道卫生服务中心","B街道卫生服务中心","C街道卫生服务中心","D街道卫生服务中心","E街道卫生服务中心","F街道卫生服务中心","G街道卫生服务中心","H街道卫生服务中心","I街道卫生服务中心","J区疾控中心"]
scenario_set = ["弱传播_社区内_单点爆发", "弱传播_社区内_多点关联","弱传播_跨社区_多点关联","弱传播_跨街道_多点关联", "稳传播_社区内_单点爆发", "稳传播_社区内_多点关联", "稳传播_跨社区_多点关联", "稳传播_跨街道_多点关联", "强传播_社区内_多点关联", "强传播_社区内_多点散发", "强传播_跨社区_多点关联", "强传播_跨社区_多点散发", "强传播_跨街道_多点关联", "强传播_跨街道_多点散发"]
resource_set = ["医用口罩","防护服","消毒液","护目镜","帐篷","社区卫生服务中心医护人员","手套","测温仪","酒精"]
task_set = ["epidemiological investigation","disinfection","nucleic acid testing","infection or contact transfer","neighborhood entrance screening"] 
tasks_required_resources = {'epidemiological investigation': {'医用口罩', '防护服', '护目镜', '社区卫生服务中心医护人员','手套','测温仪'},'disinfection':{'医用口罩', '防护服', '消毒液', '护目镜','手套','酒精'},'nucleic acid testing':{'医用口罩', '防护服', '护目镜', '帐篷', '社区卫生服务中心医护人员','手套','酒精'},'infection or contact transfer':{'医用口罩', '防护服','护目镜','社区卫生服务中心医护人员','手套'},'neighborhood entrance screening': {'医用口罩', '防护服', '护目镜', '帐篷','手套','测温仪'}}
task_process_subject = {'epidemiological investigation': {'社区居委会', '街道卫生服务中心', '区疾控中心'},'disinfection':{'社区居委会', '社区物业'},'nucleic acid testing':{'街道卫生服务中心'},'infection or contact transfer':{'社区居委会','街道卫生服务中心'},'neighborhood entrance screening': {'社区居委会'}}
infected_neighborhood_task = ["epidemiological investigation","infection or contact transfer","neighborhood entrance screening"]
consumable_resource = ["医用口罩","防护服","消毒液","护目镜","手套","酒精"]
reusable_resource = ["帐篷","社区卫生服务中心医护人员","测温仪"]

# ------------------ 样本数据载入 ------------------ #
csv_path = "64_9_simulated_demand_structured_Ns_10.csv"
df = pd.read_csv(csv_path)

# ------------------ 主体-任务匹配表 ------------------ #
def build_subject_task_map(subject_set, task_process_subject):
    subject_task_map = {}
    for subject in subject_set:
        subject_task_map[subject] = []
        for task, valid_roles in task_process_subject.items():
            for role in valid_roles:
                if role in subject:
                    subject_task_map[subject].append(task)
                    break
    return subject_task_map

subject_task_map = build_subject_task_map(subject_set, task_process_subject)

# ------------------ 主体-区域信息 ------------------ #
subject_info = {
    0: ("a1", "A", "J"), 1: ("a1", "A", "J"),
    2: ("a2", "A", "J"), 3: ("a2", "A", "J"),
    4: ("a3", "A", "J"), 5: ("a3", "A", "J"),

    6: ("b1", "B", "J"), 7: ("b1", "B", "J"),
    8: ("b2", "B", "J"), 9: ("b2", "B", "J"),
    10: ("b3", "B", "J"), 11: ("b3", "B", "J"),

    12: ("c1", "C", "J"), 13: ("c1", "C", "J"),
    14: ("c2", "C", "J"), 15: ("c2", "C", "J"),
    16: ("c3", "C", "J"), 17: ("c3", "C", "J"),

    18: ("d1", "D", "J"), 19: ("d1", "D", "J"),
    20: ("d2", "D", "J"), 21: ("d2", "D", "J"),
    22: ("d3", "D", "J"), 23: ("d3", "D", "J"),

    24: ("e1", "E", "J"), 25: ("e1", "E", "J"),
    26: ("e2", "E", "J"), 27: ("e2", "E", "J"),
    28: ("e3", "E", "J"), 29: ("e3", "E", "J"),

    30: ("f1", "F", "J"), 31: ("f1", "F", "J"),
    32: ("f2", "F", "J"), 33: ("f2", "F", "J"),
    34: ("f3", "F", "J"), 35: ("f3", "F", "J"),

    36: ("g1", "G", "J"), 37: ("g1", "G", "J"),
    38: ("g2", "G", "J"), 39: ("g2", "G", "J"),
    40: ("g3", "G", "J"), 41: ("g3", "G", "J"),

    42: ("h1", "H", "J"), 43: ("h1", "H", "J"),
    44: ("h2", "H", "J"), 45: ("h2", "H", "J"),
    46: ("h3", "H", "J"), 47: ("h3", "H", "J"),

    48: ("i1", "I", "J"), 49: ("i1", "I", "J"),
    50: ("i2", "I", "J"), 51: ("i2", "I", "J"),
    52: ("i3", "I", "J"), 53: ("i3", "I", "J"),

    54: (None, "A", "J"),
    55: (None, "B", "J"),
    56: (None, "C", "J"),
    57: (None, "D", "J"),
    58: (None, "E", "J"),
    59: (None, "F", "J"),
    60: (None, "G", "J"),
    61: (None, "H", "J"),
    62: (None, "I", "J"),

    63: (None, None, "J")
}

# ------------------ 街道-社区映射 ------------------ #
town_to_communities = {
    "A": ["a1", "a2", "a3"],
    "B": ["b1", "b2", "b3"],
    "C": ["c1", "c2", "c3"],
    "D": ["d1", "d2", "d3"],
    "E": ["e1", "e2", "e3"],
    "F": ["f1", "f2", "f3"],
    "G": ["g1", "g2", "g3"],
    "H": ["h1", "h2", "h3"],
    "I": ["i1", "i2", "i3"],
}

# ------------------ 情景感染社区 ------------------ #
infected_communities = {
    1: {"a1"},
    2: {"a1"},
    3: {"a1", "a2"},
    4: {"a1", "b1"},
    5: {"a1"},
    6: {"a1"},
    7: {"a1", "a2"},
    8: {"a1", "b1"},
    9: {"a1"},
    10: {"a1"},
    11: {"a1", "a2"},
    12: {"a1", "a2", "a3"},
    13: {"a1", "b1"},
    14: {"a1", "b1", "c1"},
}


# ------------------ 任务主体匹配辅助函数 ------------------ #
def extract_region(subject_name):
    for level_name in ["社区", "街道", "区"]:
        if level_name in subject_name:
            prefix = subject_name.split(level_name)[0]
            return prefix, level_name
    return None, None

# ------------------ 情景-主体-任务映射 ------------------ #
def build_scenario_subject_tasks(S, subject_set, infected_communities, town_to_communities, subject_task_map):
    scenario_subject_tasks = {}
    for s in range(1, S + 1):
        scenario_subject_tasks[s] = {}
        infected = infected_communities[s]
        for subject in subject_set:
            region, level_name = extract_region(subject)
            available_tasks = subject_task_map.get(subject, [])
            executed_tasks = []
            for task in available_tasks:
                if task in infected_neighborhood_task:
                    if level_name == "社区" and region in infected:
                        executed_tasks.append(task)
                    elif level_name == "街道" and any(com in infected for com in town_to_communities.get(region, [])):
                        executed_tasks.append(task)
                    elif level_name == "区":
                        executed_tasks.append(task)
                else:
                    executed_tasks.append(task)
            scenario_subject_tasks[s][subject] = executed_tasks
    return scenario_subject_tasks

scenario_subject_tasks = build_scenario_subject_tasks(S, subject_set, infected_communities, town_to_communities, subject_task_map)


# ------------------ 获取主体角色 ------------------ #
def get_subject_role(subject_name):
    for role in {"社区居委会", "社区物业", "街道卫生服务中心", "区疾控中心"}:
        if role in subject_name:
            return role
    return None

# ------------------ 提供者限定资源 ------------------ #
resource_to_provider = {
    "帐篷": "社区居委会",
    "社区卫生服务中心医护人员": "街道卫生服务中心"
}

# ------------------ 构造资源使用映射 scenario_subject_resources ------------------ #
def build_scenario_subject_resources(scenario_subject_tasks, subject_set):
    scenario_subject_resources = {}
    for s in scenario_subject_tasks:
        scenario_subject_resources[s] = {}
        for subject in subject_set:
            role = get_subject_role(subject)
            tasks = scenario_subject_tasks[s].get(subject, [])
            used_resources = set()
            for task in tasks:
                required_resources = tasks_required_resources.get(task, set())
                eligible_roles = task_process_subject.get(task, set())
                if role in eligible_roles:
                    for res in required_resources:
                        if res in resource_to_provider:
                            if role == resource_to_provider[res]:
                                used_resources.add(res)
                        else:
                            used_resources.add(res)
            scenario_subject_resources[s][subject] = used_resources
    return scenario_subject_resources

scenario_subject_resources = build_scenario_subject_resources(scenario_subject_tasks, subject_set)


# ------------------ 主体地理位置与距离矩阵 ------------------ #
subject_location = {
    "0": {"latitude": 30.586742751035548, "longitude": 114.26706028528116},
    "1": {"latitude": 30.591059393200215, "longitude": 114.26832588446237},
    "2": {"latitude": 30.593122799594283, "longitude": 114.26150942152913},
    "3": {"latitude": 30.59320122037391, "longitude": 114.26103027080316},
    "4": {"latitude": 30.58734770588274, "longitude": 114.26151418342828},
    "5": {"latitude": 30.589174498871245, "longitude": 114.26605136610937},
    "6": {"latitude": 30.6105534444227, "longitude": 114.24374676467106},
    "7": {"latitude": 30.61509553337032, "longitude": 114.24717998713714},
    "8": {"latitude": 30.61473083101024, "longitude": 114.26101273323361},
    "9": {"latitude": 30.610447270786157, "longitude": 114.26410264313097},
    "10": {"latitude": 30.6066795119465, "longitude": 114.242165992759},
    "11": {"latitude": 30.6049157276533, "longitude": 114.243206689545},
    "12": {"latitude": 30.585106878789794, "longitude": 114.27947048407667},
    "13": {"latitude": 30.5862693050447, "longitude": 114.27722436444527},
    "14": {"latitude": 30.588714748028178, "longitude": 114.2785990485121},
    "15": {"latitude": 30.588340572314234, "longitude": 114.27825113196386},
    "16": {"latitude": 30.5835247449999, "longitude": 114.280929821395},
    "17": {"latitude": 30.583303131947, "longitude": 114.280489179155},
    "18": {"latitude": 30.568501778957, "longitude": 114.293480692616},
    "19": {"latitude": 30.569857440433, "longitude": 114.293245912202},
    "20": {"latitude": 30.572062010967, "longitude": 114.289154692616},
    "21": {"latitude": 30.571026338226, "longitude": 114.287397369873},
    "22": {"latitude": 30.571149382527, "longitude": 114.290196317968},
    "23": {"latitude": 30.570550250996, "longitude": 114.292700998166},
    "24": {"latitude": 30.627292159543, "longitude": 114.263926506189},
    "25": {"latitude": 30.628855094345, "longitude": 114.262609617794},
    "26": {"latitude": 30.617557636540, "longitude": 114.240707912203},
    "27": {"latitude": 30.617685004740, "longitude": 114.241787571801},
    "28": {"latitude": 30.621523094426, "longitude": 114.244028252139},
    "29": {"latitude": 30.619586468130, "longitude": 114.245071523303},

    "30": {"latitude": 30.5792998402753, "longitude": 114.2764235391880},
    "31": {"latitude": 30.5788856377503, "longitude": 114.2770957711610},
    "32": {"latitude": 30.5778315125511, "longitude": 114.2819218124590},
    "33": {"latitude": 30.5789523372059, "longitude": 114.2806323667860},
    "34": {"latitude": 30.5763624819868, "longitude": 114.2839498514030},
    "35": {"latitude": 30.5759052488022, "longitude": 114.2824531788200},
    "36": {"latitude": 30.5732170073941, "longitude": 114.2834361129340},
    "37": {"latitude": 30.5731499109439, "longitude": 114.2834501873200},
    "38": {"latitude": 30.5722968596230, "longitude": 114.2811979122020},
    "39": {"latitude": 30.5739820887053, "longitude": 114.2825218507320},
    "40": {"latitude": 30.5708705632524, "longitude": 114.2814370797170},
    "41": {"latitude": 30.5712662843715, "longitude": 114.2805691675490},

    "42": {"latitude": 30.6192233321996, "longitude": 114.2635049135100},
    "43": {"latitude": 30.6183862378800, "longitude": 114.2663233008300},
    "44": {"latitude": 30.6154270404604, "longitude": 114.2763502693320},
    "45": {"latitude": 30.6117828158383, "longitude": 114.2763045391880},
    "46": {"latitude": 30.6218933014113, "longitude": 114.2681335404960},
    "47": {"latitude": 30.6201220276100, "longitude": 114.2599718300830},
    "48": {"latitude": 30.5749184812020, "longitude": 114.2903848975730},
    "49": {"latitude": 30.5732364687922, "longitude": 114.2935230488520},
    "50": {"latitude": 30.5724575666544, "longitude": 114.2874259703540},
    "51": {"latitude": 30.5735772134298, "longitude": 114.2878259978500},
    "52": {"latitude": 30.5744539972648, "longitude": 114.2932116157090},
    "53": {"latitude": 30.5747095953591, "longitude": 114.2931190430430},

    "54": {"latitude": 30.592643567069132, "longitude": 114.26897206080108},###
    "55": {"latitude": 30.607724089167778, "longitude": 114.24595061932298},
    "56": {"latitude": 30.588413726034446, "longitude": 114.28072056359557},
    "57": {"latitude": 30.5715877742531, "longitude": 114.286392709809},
    "58": {"latitude": 30.632290963781, "longitude": 114.262523790961},
    "59": {"latitude": 30.5766873734816, "longitude": 114.279454540495},
    "60": {"latitude": 30.571845905886, "longitude": 114.282696692616},
    "61": {"latitude": 30.6143868096293, "longitude": 114.273132454531},
    "62": {"latitude": 30.576415003916, "longitude": 114.289719727002},
    "63": {"latitude": 30.61190702367985, "longitude": 114.26500075726067},
}

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def compute_subject_distance(subject_location_dict, N):
    distance_matrix = np.zeros((N, N))
    for i in range(N):
        lat_i = subject_location_dict[str(i)]["latitude"]
        lon_i = subject_location_dict[str(i)]["longitude"]
        for j in range(N):
            lat_j = subject_location_dict[str(j)]["latitude"]
            lon_j = subject_location_dict[str(j)]["longitude"]
            if i != j:
                distance = haversine_distance(lat_i, lon_i, lat_j, lon_j)
                distance_matrix[i, j] = round(distance, 4)
    return pd.DataFrame(distance_matrix, index=range(N), columns=range(N)), distance_matrix

distance_df, distance_df_numpy = compute_subject_distance(subject_location, N)


# ------------------ 主体在不同情景下的需求等级系数匹配 ------------------
def build_w_matrix(subject_info, level_table, infected_communities, demand_coefficient):
    w = {}
    for scenario, infected in infected_communities.items():
        w[scenario] = {}
        for subj, (comm, town, district) in subject_info.items():
            if comm is not None:
                if comm in infected:
                    level_key = 1
                elif town and any(c in infected for c in town_to_communities[town]):
                    level_key = 2
                else:
                    level_key = 3
            elif town is not None:
                town_comms = town_to_communities[town]
                level_key = "T1" if all(c not in infected for c in town_comms) else "T2"
            else:
                level_key = "D"

            level_text = level_table[scenario][level_key]
            w[scenario][subj] = demand_coefficient[level_text]
    df_w = pd.DataFrame(w).T
    return df_w

demand_coefficient = {
    "很低": 1,
    "较低": 2,
    "一般": 3,
    "较高": 4,
    "很高": 5
}

level_table = {
    1: {1: "较低", 2: "很低", 3: "很低", "T1": "很低", "T2": "较低", "D": "较低"},
    2: {1: "较低", 2: "很低", 3: "很低", "T1": "很低", "T2": "较低", "D": "较低"},
    3: {1: "较低", 2: "很低", 3: "很低", "T1": "很低", "T2": "较低", "D": "较低"},
    4: {1: "较低", 2: "很低", 3: "很低", "T1": "较低", "T2": "较低", "D": "较低"},
    5: {1: "一般", 2: "较低", 3: "很低", "T1": "很低", "T2": "较低", "D": "较低"},
    6: {1: "一般", 2: "较低", 3: "较低", "T1": "较低", "T2": "一般", "D": "一般"},
    7: {1: "一般", 2: "较低", 3: "较低", "T1": "一般", "T2": "一般", "D": "一般"},
    8: {1: "较高", 2: "一般", 3: "一般", "T1": "一般", "T2": "较高", "D": "较高"},
    9: {1: "一般", 2: "较低", 3: "较低", "T1": "较低", "T2": "一般", "D": "一般"},
    10: {1: "一般", 2: "一般", 3: "一般", "T1": "一般", "T2": "一般", "D": "一般"},
    11: {1: "较高", 2: "一般", 3: "较低", "T1": "较低", "T2": "较高", "D": "较高"},
    12: {1: "很高", 2: "较高", 3: "一般", "T1": "一般", "T2": "很高", "D": "很高"},
    13: {1: "较高", 2: "一般", 3: "一般", "T1": "一般", "T2": "较高", "D": "较高"},
    14: {1: "很高", 2: "较高", 3: "较高", "T1": "较高", "T2": "很高", "D": "很高"},
}
df_w = build_w_matrix(subject_info, level_table, infected_communities, demand_coefficient)


hir_t0 = np.array([
    [50, 10, 10, 10, 2, 0, 50, 2, 10],  
    [60, 20, 50, 20, 2, 0, 10, 2, 20], 
    [60, 10, 10, 10, 1, 0, 60, 1, 10],  
    [70, 22, 36, 22, 1, 0, 70, 1, 22], 
    [60, 20, 20, 16, 3, 0, 60, 3, 16],  
    [74, 28, 54, 28, 2, 0, 74, 2, 28],
    [56, 12, 15, 12, 2, 0, 56, 2, 12],
    [66, 24, 45, 24, 2, 0, 66, 2, 24], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [78, 26, 56, 26, 3, 0, 78, 3, 26],   
    [76, 26, 50, 26, 1, 0, 76, 1, 26],
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [56, 12, 15, 12, 2, 0, 56, 2, 12],
    [66, 24, 45, 24, 2, 0, 66, 2, 24], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [78, 26, 56, 26, 3, 0, 78, 3, 26],   
    [76, 26, 50, 26, 1, 0, 76, 1, 26],
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [56, 12, 15, 12, 2, 0, 56, 2, 12],
    [66, 24, 45, 24, 2, 0, 66, 2, 24], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [78, 26, 56, 26, 3, 0, 78, 3, 26],   
    [76, 26, 50, 26, 1, 0, 76, 1, 26],
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [56, 12, 15, 12, 2, 0, 56, 2, 12],
    [66, 24, 45, 24, 2, 0, 66, 2, 24], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [90, 42, 40, 42, 2, 0, 90, 2, 42],
    [102, 50, 78, 50, 2, 0, 102, 2, 50], 
    [78, 26, 56, 26, 3, 0, 78, 3, 26],   
    [76, 26, 50, 26, 1, 0, 76, 1, 26],
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [97, 45, 38, 45, 2, 0, 97, 2, 45],   
    [110, 52, 82, 52, 2, 0, 110, 2, 52], 
    [100, 26, 40, 26, 3, 10, 100, 3, 26], 
    [120, 30, 30, 20, 3, 16, 120, 3, 20],
    [130, 24, 36, 22, 3, 18, 130, 3, 22],
    [150, 50, 70, 50, 4, 0, 150, 4, 50],  
    [130, 24, 36, 22, 3, 18, 130, 3, 22],
    [150, 50, 70, 50, 4, 0, 150, 4, 50],  
    [130, 24, 36, 22, 3, 18, 130, 3, 22],
    [150, 50, 70, 50, 4, 0, 150, 4, 50],  
    [130, 24, 36, 22, 3, 18, 130, 3, 22],
    [150, 50, 70, 50, 4, 0, 150, 4, 50] 
]) 

k_ir =  np.array([
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200], 
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 200, 200, 200, 0, 200, 200, 200],  
    [300, 200, 200, 200, 200, 0, 300, 200, 200],
    [200, 200, 0, 200, 0, 200, 200, 200, 200], 
    [200, 200, 0, 200, 0, 200, 200, 200, 200], 
    [200, 200, 0, 200, 0, 200, 200, 200, 200], 
    [200, 200, 0, 200, 0, 200, 200, 200, 200], 
    [200, 200, 0, 200, 0, 200, 200, 200, 200], 
    [200, 200, 0, 200, 0, 200, 200, 200, 200], 
    [200, 200, 0, 200, 0, 200, 200, 200, 200],
    [200, 200, 0, 200, 0, 200, 200, 200, 200], 
    [200, 200, 0, 200, 0, 200, 200, 200, 200],
    [200, 200, 0, 200, 0, 0, 200, 200, 200]  
]) 


# ------------------ 外部支援构建函数girt ------------------ #
## t=0 external assistance rules
external_assistance_rules_t0 = {
    "neighbourhood_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "帐篷": 0, "手套": 0, "测温仪": 0, "酒精": 0},
    "property_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "手套": 0, "测温仪": 0, "酒精": 0},
    "town_subject": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "社区卫生服务中心医护人员": 0, "手套": 0, "测温仪": 0, "酒精": 0},
    "district_subject": {"医用口罩": 0, "防护服": 0, "护目镜": 0, "手套": 0, "测温仪": 0, "酒精": 0}
}
##t1也没有得到外部支援
external_assistance_rules_t1 = {
    "neighbourhood_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "帐篷": 0, "手套": 0, "测温仪": 0, "酒精": 0},
    "property_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "手套": 0, "测温仪": 0, "酒精": 0},
    "town_subject": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "社区卫生服务中心医护人员": 0, "手套": 0, "测温仪": 0, "酒精": 0},
    "district_subject": {"医用口罩": 0, "防护服": 0, "护目镜": 0, "手套": 0, "测温仪": 0, "酒精": 0}
}

# 主体分组（ID是字符串）
neighbourhood_committee = ["0","2","4","6","8","10","12","14","16","18","20","22","24","26","28","30","32","34","36","38","40","42","44","46","48","50","52"]
property_committee = [ "1","3","5","7","9","11","13","15","17","19","21","23","25","27","29","31","33","35","37","39","41","43","45","47","49","51","53"]
town_subject = ["54","55","56","57","58","59","60","61","62"]
district_subject = ["63"]

def generate_external_support(subject_ids, role_groups, rules):
    gir = {subj: {r: 0 for r in resource_set} for subj in subject_ids}
    for subj in subject_ids:
        if subj in role_groups["neighbourhood_committee"]:
            for res, qty in rules["neighbourhood_committee"].items():
                gir[subj][res] = qty
        if subj in role_groups["property_committee"]:
            for res, qty in rules["property_committee"].items():
                gir[subj][res] = qty
        if subj in role_groups["town_subject"]:
            for res, qty in rules["town_subject"].items():
                gir[subj][res] = qty
        if subj in role_groups["district_subject"]:
            for res, qty in rules["district_subject"].items():
                gir[subj][res] = qty
    df_gir = pd.DataFrame(gir).T.reindex(columns=resource_set).fillna(0)
    return gir, df_gir.to_numpy()

# 构建角色映射
role_groups = {
    "neighbourhood_committee": neighbourhood_committee,
    "property_committee": property_committee,
    "town_subject": town_subject,
    "district_subject": district_subject
}

# 前后两天的gir_t0
gir_t0, gir_numpy_t0 = generate_external_support(list(map(str, range(N))), role_groups, external_assistance_rules_t0)
gir_t1, gir_numpy_t1 = generate_external_support(list(map(str, range(N))), role_groups, external_assistance_rules_t1)


x_iir_t0 = np.zeros((R, N, N), dtype=int)
dir_all = df.iloc[:, 2:].to_numpy().reshape((-1, N, R)) 
# ------------------ t=0资源状态计算：bir_t0, hir_t1 ------------------ #
def compute_resource_consumption_t0(hir_t0, gir_numpy_t0, x_iir_t0, dir_all, scenario_t0=1, N_s=10):
    shared_in_t0 = x_iir_t0.sum(axis=1).T 
    shared_out_t0 = x_iir_t0.sum(axis=2).T
    left_sum_t0 = hir_t0 + gir_numpy_t0 + shared_in_t0 - shared_out_t0
    sample_id = 0
    index_t0 = (scenario_t0 - 1) * N_s + sample_id 
    dir_ns = dir_all[index_t0]  
    bir_t0 = np.minimum(left_sum_t0, dir_ns) 
    bir_t0  = np.maximum(bir_t0 , 0) 
    hir_ns_t1 = np.zeros_like(hir_t0)
    consumable_indices = [i for i, name in enumerate(resource_set) if name in consumable_resource]
    reusable_indices = [i for i, name in enumerate(resource_set) if name in reusable_resource]
    if consumable_indices:
        hir_ns_t1[:, consumable_indices] = np.maximum(
            hir_t0[:, consumable_indices]
            + gir_numpy_t0[:, consumable_indices]
            + shared_in_t0[:, consumable_indices]
            - shared_out_t0[:, consumable_indices]
            - bir_t0[:, consumable_indices], 0
        ) 
    if reusable_indices:
        hir_ns_t1[:, reusable_indices] = np.maximum(
            hir_t0[:, reusable_indices]
            + gir_numpy_t0[:, reusable_indices]
            + shared_in_t0[:, reusable_indices]
            - shared_out_t0[:, reusable_indices], 0
        ) 
    return bir_t0, hir_ns_t1
bir_t0, hir_ns_t1 = compute_resource_consumption_t0(hir_t0, gir_numpy_t0, x_iir_t0, dir_all, scenario_t0=1, N_s=10) 

# ------------------ 保存前一天bir_t0, 当天结束的hir_t1 为csv------------------ #
def save_bir_and_hir_to_csv(bir_t0, hir_ns_t1, N, R):
    def build_dataframe(mat, label):
        df = pd.DataFrame(mat.reshape(N, R))
        df.columns = [f"R{r+1}" for r in range(R)]
        df.insert(0, "subject_id", [f"P{i+1:02}" for i in range(N)])
        return df

    bir_df = build_dataframe(bir_t0, "bir_t0")
    hir_df = build_dataframe(hir_ns_t1, "hir_t1")

    bir_df.to_csv("bir_t0.csv", index=False)
    hir_df.to_csv("hir_t1.csv", index=False)

    print("Saved: bir_t0.csv and hir_t1.csv")


available_sharing_t1 = gir_numpy_t1 + hir_ns_t1 
scenario_array = df['scenario'].to_numpy()
sample_id_array = df['sample_id'].to_numpy()
bir_t0, hir_ns_t1 = compute_resource_consumption_t0(hir_t0, gir_numpy_t0, x_iir_t0, dir_all)

# ------------------ 构造qir_ns_t1：样本下的对外真实需求 ------------------ #
def build_qir_ns_t1(S, scenario_array, sample_id_array, dir_all, hir_ns_t1, gir_numpy_t1):
    qir_ns_t1 = {}
    for s in range(1, S + 1):
        indices = np.where(scenario_array == s)[0]
        qir_ns_t1[s] = {}
        for idx in indices:
            sample_id = sample_id_array[idx]
            dir_ns = dir_all[idx]
            qir_matrix = np.maximum(dir_ns - hir_ns_t1 - gir_numpy_t1, 0)
            qir_ns_t1[s][sample_id] = qir_matrix
    return qir_ns_t1

qir_ns_t1 = build_qir_ns_t1(S, scenario_array, sample_id_array, dir_all, hir_ns_t1, gir_numpy_t1)

# ------------------ 情景概率载入函数 ------------------ #
def get_scenario_prob(day, csv_path="../../Sample_data/scenario_probability_Marcov.csv"):
    df = pd.read_csv(csv_path, index_col="Day")
    return df.loc[day].to_numpy()

t = 1  
scenario_prob_t = get_scenario_prob(t)

# ------------------ 模糊集半径 theta_s ------------------ #
theta_s = np.array([3.27, 3.30, 3.37, 3.37, 3.26, 3.55, 3.56, 3.53, 3.47, 3.49, 3.52, 3.53, 3.51, 3.56])


# ====================== 决策变量 ======================
def define_cvxpy_variables() -> tuple[list[cp.Variable], list[cp.Variable], cp.Variable, cp.Variable]:
    """x: (R 个 N*N) 比例矩阵, non-neg;  fai: 同维度 bool;  pai: (S,N_s);  γ: (S,)"""
    x_iir_t1 = [cp.Variable((N, N), nonneg=True, name=f"x_r{r}") for r in range(R)]
    fai_t1 = [cp.Variable((N, N), boolean=True, name=f"fai_r{r}") for r in range(R)]
    pai_t1 = cp.Variable((S, N_s), name="pai_t1")
    gamma_t1 = cp.Variable(S, name="gamma_t1")
    return x_iir_t1, fai_t1, pai_t1, gamma_t1


# ======================  约束构造 ======================
def flatten_w_matrix(df_w, R):
    w_broad = np.repeat(df_w.values[:, :, np.newaxis], R, axis=2)  
    w_flat = w_broad.reshape(14, -1)  
    columns = [f"P{i:02d}_R{r+1}" for i in range(N) for r in range(R)]
    w_broad_df = pd.DataFrame(w_flat, index=df_w.index, columns=columns)
    w_matrix = [w_broad_df.iloc[s].values.reshape(N, R) for s in range(S)]
    return w_matrix, w_flat

w_matrix, w_flat = flatten_w_matrix(df_w, R)

# ------------------ 构造共享矩阵 shared_in / shared_out ------------------ #
def build_shared_matrices(x_iir_t1: list[cp.Expression], available_sharing_t1: np.ndarray) -> tuple[cp.Expression, cp.Expression]:
    """返回 (N,R) 的 shared_in / shared_out 绝对数量表达式"""
    shared_in, shared_out = [], []
    for r in range(R):
        abs_mat = cp.multiply(x_iir_t1[r], available_sharing_t1[:, r][:, None])  # (N,N)
        shared_in.append(cp.sum(abs_mat, axis=0))   
        shared_out.append(cp.sum(abs_mat, axis=1))  
    return cp.vstack(shared_in).T, cp.vstack(shared_out).T  # 均为 (N,R)


# ------------------ 构造距离矩阵乘以是否共享的总运输距离 ------------------ #
def build_total_transport_cost(fai_t1, distance_matrix: np.ndarray) -> cp.Expression:
    total_cost = 0
    for r in range(R):
        total_cost += cp.sum(cp.multiply(fai_t1[r], distance_matrix))
    return lamda * total_cost

def build_constraints(
    x_iir_t1, fai_t1, pai_t1, gamma_t1,
    k_ir, w_matrix, w_flat,
    shared_in, shared_out,
    dir_all, hir_ns_t1, gir_numpy_t1,
    total_transport_cost,
    qir_ns_t1, theta_s,
    scenario_array, sample_id_array, scenario_prob_t
):
    constraints = []
    S = len(theta_s)
    R, N = len(x_iir_t1), x_iir_t1[0].shape[0]

    aux_transport = cp.Variable(name="aux_transport")
    constraints += [aux_transport == total_transport_cost]

    # Constraint 1:
    epsilon = 1e-5  
    M = 10000
    for r in range(R):
        constraints += [
            x_iir_t1[r] <= M * fai_t1[r],
            x_iir_t1[r] >= epsilon * fai_t1[r],
            x_iir_t1[r] >= 0, 
            x_iir_t1[r] <= 1
        ]

    # Constraint 2:
    for s in range(1, S + 1):
        w_s = w_matrix[s - 1]                   
        kw_s = k_ir * w_s                  
        const_part2 = -np.sum(kw_s * (hir_ns_t1 + gir_numpy_t1))
        indices = np.where(scenario_array == s)[0]
        for idx in indices:
            sid = sample_id_array[idx]
            dir_ns = dir_all[idx]               
            lhs_val = -np.sum(kw_s * dir_ns)   
            var_rhs = -cp.sum(cp.multiply(kw_s, shared_in))
            rhs = -pai_t1[s - 1, sid] + const_part2 + var_rhs + aux_transport
            constraints += [lhs_val >= rhs]

    # Constraint 3:
    gamma_lb = [float(np.linalg.norm((k_ir * w_matrix[s - 1]).flatten(), 2)) for s in range(1, S + 1)]
    for s in range(1, S + 1):
        constraints += [gamma_t1[s - 1] >= gamma_lb[s - 1]]

    # Constraint 4: 
    for s in range(1, S + 1):
        w_s = w_matrix[s - 1]
        kw_s = k_ir * w_s
        indices = np.where(scenario_array == s)[0]
        for idx in indices:
            sid = sample_id_array[idx]
            var_expr = -cp.sum(cp.multiply(kw_s, shared_in))
            rhs  = -pai_t1[s - 1, sid] + var_expr + aux_transport
            constraints += [rhs <= 0]

    # Constraint 5: 
    for s in range(1, S + 1):
        indices = np.where(scenario_array == s)[0]
        for idx in indices:
            sid = sample_id_array[idx]
            constraints += [-pai_t1[s - 1, sid] + aux_transport <= 0]

    # Constraint 6: 
    accum = 0
    for s in range(1, S + 1):
        prob = scenario_prob_t[s - 1]
        theta_val = theta_s[s - 1]
        q_sum = 0
        count = 0
        for idx in np.where(scenario_array == s)[0]:
            q_mat = qir_ns_t1[s][sample_id_array[idx]]
            q_sum += q_mat
            count += 1
        q_mean = q_sum / count
        robust_lower_q = np.maximum(q_mean - theta_val, 0)
        accum += prob * robust_lower_q
    constraints += [accum >= shared_in]

    # Constraint 7: 
    constraints += [hir_ns_t1 + gir_numpy_t1 - shared_out >= 0]

    # Constraint 8: 
    for r in range(R):
        constraints += [cp.diag(x_iir_t1[r]) == 0]
    
    # Constraint 9: 
    l_ir = [cp.Variable(N, boolean=True, name=f"l_r{r}") for r in range(R)]
    for r in range(R):
        out_vec = cp.sum(x_iir_t1[r], axis=1) 
        in_vec  = cp.sum(x_iir_t1[r], axis=0) 
        constraints += [
            out_vec <= 10 * (1 - l_ir[r]), 
            in_vec  <= 10 * l_ir[r]
        ]
    return constraints

# ====================== 目标函数 ====================== 
def build_objective(pai_t1, gamma_t1, scenario_prob, theta_s):
    weights_sample = np.repeat(scenario_prob / N_s, N_s) 
    objective_section1 = cp.sum(cp.multiply(cp.vec(pai_t1), weights_sample))
    objective_section2 = cp.sum(cp.multiply(gamma_t1, scenario_prob * theta_s))
    return cp.Minimize(objective_section1 + objective_section2), objective_section1, objective_section2

# ====================== 模型求解函数 ====================== #
def solve_dro_ratio_model(
    k_ir, w_matrix, w_flat,
    hir_ns_t1, gir_numpy_t1, available_sharing_t1,
    qir_ns_t1, theta_s, scenario_prob_t,
    distance_matrix
):
    x_iir_t1, fai_t1, pai_t1, gamma_t1 = define_cvxpy_variables()

    shared_in, shared_out = build_shared_matrices(x_iir_t1, available_sharing_t1)

    transport_cost = build_total_transport_cost(fai_t1, distance_matrix)

    constraints = build_constraints(
        x_iir_t1, fai_t1, pai_t1, gamma_t1,
        k_ir, w_matrix, w_flat,
        shared_in, shared_out,
        dir_all, hir_ns_t1, gir_numpy_t1,
        transport_cost,
        qir_ns_t1, theta_s,
        scenario_array, sample_id_array, scenario_prob_t
    )

    objective,objective_section1,objective_section2 = build_objective(pai_t1, gamma_t1, scenario_prob_t, theta_s)

    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.GUROBI, verbose=True)

    return {
        "problem": problem,
        "x_iir_t1": x_iir_t1,
        "fai_t1": fai_t1,
        "pai_t1": pai_t1,
        "gamma_t1": gamma_t1,
        "transport_cost":transport_cost, 
        "objective": objective,
        "objective_section1": objective_section1,
        "objective_section2": objective_section2,
        "transport_cost":  transport_cost, 
        "shared_in": shared_in.value,         
        "shared_out": shared_out.value   
    }

result = solve_dro_ratio_model(k_ir, w_matrix, w_flat,
        hir_ns_t1, gir_numpy_t1, available_sharing_t1,
        qir_ns_t1, theta_s, scenario_prob_t,
        distance_df_numpy
    )

print("Objective value:", result["problem"].value)
print("Objective_section1 value:", result["objective_section1"].value)
print("Objective_section2 value:", result["objective_section2"].value)
print("Objective status:", result["problem"].status)


overall_x_iir_t1 = []
for r in range(R):
    x_r = result["x_iir_t1"][r].value  # shape: (N, N)
    for i in range(N):
        overall_x_iir_t1.append([r] + x_r[i].tolist())  
columns = ["r"] + [f"P{j}" for j in range(N)]
df = pd.DataFrame(overall_x_iir_t1, columns=columns)
df.to_csv("缩放1_x_iir_t1_stacked_with_r.csv", index=False)