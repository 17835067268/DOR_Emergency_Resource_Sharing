import numpy as np
import pandas as pd
import cvxpy as cp
import gurobipy as gp


# ======================  参数设定 ======================  
N, R = 18, 6
N_s = 10
S = 14
lamda = 1600 #单位元。1km花费500元


subject_set = ["a1社区居委会","a1社区物业","a2社区居委会","a2社区物业","a3社区居委会","a3社区物业","b1社区居委会","b1社区物业","b2社区居委会","b2社区物业","c1社区居委会","c1社区物业","c2社区居委会","c2社区物业","A街道卫生服务中心","B街道卫生服务中心","C街道卫生服务中心","D区疾控中心"]
scenario_set = ["弱传播_社区内_单点爆发", "弱传播_社区内_多点关联","弱传播_跨社区_多点关联","弱传播_跨街道_多点关联", "稳传播_社区内_单点爆发", "稳传播_社区内_多点关联", "稳传播_跨社区_多点关联", "稳传播_跨街道_多点关联", "强传播_社区内_多点关联", "强传播_社区内_多点散发", "强传播_跨社区_多点关联", "强传播_跨社区_多点散发", "强传播_跨街道_多点关联", "强传播_跨街道_多点散发"]
resource_set = ["医用口罩","防护服","消毒液","护目镜","帐篷","社区卫生服务中心医护人员"]
task_set = ["epidemiological investigation","disinfection","nucleic acid testing","infection or contact transfer","neighborhood entrance screening"] 
tasks_required_resources = {'epidemiological investigation': {'医用口罩', '防护服', '护目镜', '社区卫生服务中心医护人员'},'disinfection':{'医用口罩', '防护服', '消毒液', '护目镜'},'nucleic acid testing':{'医用口罩', '防护服', '护目镜', '帐篷','社区卫生服务中心医护人员'},'infection or contact transfer':{'医用口罩', '防护服','护目镜','社区卫生服务中心医护人员'},'neighborhood entrance screening': {'医用口罩', '防护服', '护目镜', '帐篷'}}
task_process_subject = {'epidemiological investigation': {'社区居委会', '街道卫生服务中心', '区疾控中心'},'disinfection':{'社区居委会', '社区物业'},'nucleic acid testing':{'街道卫生服务中心'},'infection or contact transfer':{'社区居委会','街道卫生服务中心'},'neighborhood entrance screening': {'社区居委会'}}
infected_neighborhood_task = ["epidemiological investigation","infection or contact transfer","neighborhood entrance screening"]
consumable_resource = ["医用口罩","防护服","消毒液","护目镜"]
reusable_resource = ["帐篷","社区卫生服务中心医护人员"]

# ------------------ 样本数据载入(样本内) ------------------ #
csv_path = "/Sample_data/simulated_demand_structured_Ns_10.csv"
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
    0: ("a1", "A", "D"), 1: ("a1", "A", "D"),
    2: ("a2", "A", "D"), 3: ("a2", "A", "D"),
    4: ("a3", "A", "D"), 5: ("a3", "A", "D"),
    6: ("b1", "B", "D"), 7: ("b1", "B", "D"),
    8: ("b2", "B", "D"), 9: ("b2", "B", "D"),
    10: ("c1", "C", "D"), 11: ("c1", "C", "D"),
    12: ("c2", "C", "D"), 13: ("c2", "C", "D"),
    14: (None, "A", "D"), 15: (None, "B", "D"), 16: (None, "C", "D"),
    17: (None, None, "D")
}

# ------------------ 街道-社区映射 ------------------ #
town_to_communities = {
    "A": ["a1", "a2", "a3"],
    "B": ["b1", "b2"],
    "C": ["c1", "c2"]
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
    "10": {"latitude": 30.585106878789794, "longitude": 114.27947048407667},
    "11": {"latitude": 30.5862693050447, "longitude": 114.27722436444527},
    "12": {"latitude": 30.588714748028178, "longitude": 114.2785990485121},
    "13": {"latitude": 30.588340572314234, "longitude": 114.27825113196386},
    "14": {"latitude": 30.592643567069132, "longitude": 114.26897206080108},
    "15": {"latitude": 30.607724089167778, "longitude": 114.24595061932298},
    "16": {"latitude": 30.588413726034446, "longitude": 114.28072056359557},
    "17": {"latitude": 30.61190702367985, "longitude": 114.26500075726067},
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """计算两点间的球面距离, 单位为km"""
    R = 6371  # 地球半径
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

distance_df, distance_df_numpy = compute_subject_distance(subject_location, N) #单位km


# ------------------ 18主体在不同情景下的需求等级系数匹配 ------------------
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

k_ir =  np.array([
    [200, 200, 200, 200, 200, 0],  
    [300, 200, 200, 200, 200, 0], 
    [200, 200, 200, 200, 200, 0],  
    [300, 200, 200, 200, 200, 0],
    [200, 200, 200, 200, 200, 0],  
    [300, 200, 200, 200, 200, 0],
    [200, 200, 200, 200, 200, 0],  
    [300, 200, 200, 200, 200, 0],
    [200, 200, 200, 200, 200, 0],  
    [300, 200, 200, 200, 200, 0],
    [200, 200, 200, 200, 200, 0],  
    [300, 200, 200, 200, 200, 0],
    [200, 200, 200, 200, 200, 0],  
    [300, 200, 200, 200, 200, 0],
    [200, 200, 0, 200, 0, 200], 
    [200, 200, 0, 200, 0, 200], 
    [200, 200, 0, 200, 0, 200], 
    [200, 200, 0, 200, 0, 0] 
]) 

hir_t1 = np.array([
    [25,  2,  2,  1, 2,  0],
    [22,  7, 20,  8, 2,  0],
    [48,  6,  5,  7, 1,  0],
    [53, 16, 17, 16, 1,  0],
    [49, 16, 15, 12, 3,  0],
    [56, 22, 34, 22, 2,  0],
    [45,  8, 10,  8, 2,  0],
    [48, 17, 25, 18, 2,  0],
    [77, 38, 35, 39, 2,  0],
    [85, 44, 58, 44, 2,  0],
    [66, 22, 51, 22, 3,  0],
    [58, 20, 30, 21, 1,  0],
    [85, 41, 33, 41, 2,  0],
    [91, 46, 63, 46, 2,  0],
    [76, 17, 40, 18, 3, 10],
    [87, 17, 30,  6, 3, 16],
    [93, 13, 36, 10, 3, 18],
    [99, 37, 70, 33, 4,  0]
])

# ------------------ 外部支援构建函数girt ------------------ #
# t=1 external assistance rules
external_assistance_rules_t1 = {
    "neighbourhood_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "帐篷": 0},
    "property_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0,},
    "town_subject": {"医用口罩": 0, "防护服": 0, "护目镜": 0, "社区卫生服务中心医护人员": 0},
    "district_subject": {"医用口罩": 0, "防护服": 0, "护目镜": 0}
}
##t2也没有得到外部支援
external_assistance_rules_t2 = {
    "neighbourhood_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0, "帐篷": 0},
    "property_committee": {"医用口罩": 0, "防护服": 0, "消毒液": 0, "护目镜": 0,},
    "town_subject": {"医用口罩": 0, "防护服": 0, "护目镜": 0, "社区卫生服务中心医护人员": 0},
    "district_subject": {"医用口罩": 0, "防护服": 0, "护目镜": 0}
}

# 主体分组（ID是字符串）
neighbourhood_committee = ["0","2","4","6","8","10","12"]
property_committee = ["1","3","5","7","9","11","13"]
town_subject = ["14","15","16"]
district_subject = ["17"]

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


# 前后两天的gir_t1
gir_t1, gir_numpy_t1 = generate_external_support(list(map(str, range(N))), role_groups, external_assistance_rules_t1)
gir_t2, gir_numpy_t2 = generate_external_support(list(map(str, range(N))), role_groups, external_assistance_rules_t2)

available_sharing_t1 = gir_numpy_t1 + hir_t1 

##xiir比例数据读取
df_x_iir = pd.read_csv("result/x_iir_t1_stacked_with_r.csv")#读取t1时刻计算出来的x_iir_t1的数据
data_remove_first_column = df_x_iir.iloc[:, 1:].to_numpy()  
x_iir_t1 = data_remove_first_column.reshape(R, N, N)
dir_all = df.iloc[:, 2:].to_numpy().reshape((-1, N, R))
 
# ------------------ 前一天的共享情况 ------------------ #
def shared_matrices_t1(x_iir_t1, available_sharing_t1):
    """返回 (N,R) 的 shared_in / shared_out 绝对数量(NumPy实现)"""
    abs_mats = []  # 记录所有 abs_mat
    shared_in_t1 = []
    shared_out_t1 = []
    for r in range(R):
        abs_mat = x_iir_t1[r] * available_sharing_t1[:, r][:, None]  # (N,N) #前一天18个主体间针对r1-r6共享了多少数量的资源
        abs_mats.append(abs_mat)  # 新增：记录所有 abs_mat
        shared_in_t1.append(np.sum(abs_mat, axis=0))   # 列和   
        shared_out_t1.append(np.sum(abs_mat, axis=1))  # 行和 
    shared_in_t1= np.vstack(shared_in_t1).T   # shape: (N, R)
    shared_out_t1 = np.vstack(shared_out_t1).T # shape: (N, R)
    return abs_mats, shared_in_t1, shared_out_t1 

abs_mats, shared_in_t1, shared_out_t1 = shared_matrices_t1(x_iir_t1, available_sharing_t1)
abs_mats = np.rint(abs_mats).astype(int) 
shared_in_t1 = np.rint(shared_in_t1).astype(int) 
shared_out_t1 = np.rint(shared_out_t1).astype(int)

#输入准备
scenario_array = df['scenario'].to_numpy()
sample_id_array = df['sample_id'].to_numpy()

# ------------------ t=0资源状态计算：bir_t1, hir_t2 ------------------ #
def compute_resource_consumption_t1(hir_t1, gir_numpy_t1, shared_in_t1, shared_out_t1, dir_all, scenario_array, sample_id_array, resource_set, consumable_resource, reusable_resource, S):
    left_sum_t1 = hir_t1 + gir_numpy_t1 + shared_in_t1 - shared_out_t1 
    bir_t1 = {}
    hir_ns_t2 = {}
    # 设置资源类别索引
    consumable_indices = [i for i, name in enumerate(resource_set) if name in consumable_resource]
    reusable_indices = [i for i, name in enumerate(resource_set) if name in reusable_resource]
    for s in range(1, S + 1): # 遍历情景
        indices = np.where(scenario_array == s)[0] # 找出该情景 s 下所有样本的索引
        bir_t1[s] = {} # 初始化字典
        hir_ns_t2[s] = {}
        for idx in indices: # 遍历样本
            sid = sample_id_array[idx]    #[0,1] [0,1] [0,1] [0,1]...
            dir_ns = dir_all[idx]  # shape (N, R)    #[0,1] [2,3] [4,5] [6,7]...
            bir_t1_sample = np.minimum(left_sum_t1, dir_ns)
            bir_t1_sample = np.maximum(bir_t1_sample, 0) #控制bir≥0
            bir_t1[s][sid] = bir_t1_sample 
            hir_t2_sample = np.zeros_like(hir_t1)
            # 更新可消耗资源的持有量
            if consumable_indices:
                hir_t2_sample[:, consumable_indices] = np.maximum(
                    hir_t1[:, consumable_indices]
                    + gir_numpy_t1[:, consumable_indices]
                    + shared_in_t1[:, consumable_indices]
                    - shared_out_t1[:, consumable_indices]
                    - bir_t1_sample[:, consumable_indices], 0
                ) #控制hir≥0
            # 更新可重用资源的持有量（不扣除消耗）
            if reusable_indices:
                hir_t2_sample[:, reusable_indices] = np.maximum(
                    hir_t1[:, reusable_indices]
                    + gir_numpy_t1[:, reusable_indices]
                    + shared_in_t1[:, reusable_indices]
                    - shared_out_t1[:, reusable_indices], 0
                ) #控制hir≥0
            hir_ns_t2[s][sid] = hir_t2_sample
    return bir_t1, hir_ns_t2
bir_t1, hir_ns_t2 = compute_resource_consumption_t1(hir_t1, gir_numpy_t1, shared_in_t1, shared_out_t1, dir_all, scenario_array, sample_id_array, resource_set, consumable_resource, reusable_resource, S) # S*N_S个 shape (18,6)

# ------------------ 保存bir_t1, hir_t2 为csv------------------ #
def save_bir_and_hir_to_csv(bir_t1, hir_ns_t2, N, R, scenario_array, sample_id_array):
    def flatten_dict_to_rows(resource_dict, scenario_sample_ids):
        rows = []
        for s, sid in scenario_sample_ids:
            mat = resource_dict[s][sid]  # shape = (N, R)
            flat = mat.reshape(-1)
            rows.append([s, sid] + flat.tolist())
        return rows
    scenario_sample_ids = list(zip(scenario_array.tolist(), sample_id_array.tolist()))
    colnames = ["scenario", "sample_id"]
    for i in range(1, N + 1):
        for r in range(1, R + 1):
            colnames.append(f"P{i:02}_R{r}")
    # 保存 bir_t1.csv
    bir_rows = flatten_dict_to_rows(bir_t1, scenario_sample_ids)
    pd.DataFrame(bir_rows, columns=colnames).to_csv("bir_t1.csv", index=False)
    # 保存 hir_t2.csv
    hir_rows = flatten_dict_to_rows(hir_ns_t2, scenario_sample_ids)
    pd.DataFrame(hir_rows, columns=colnames).to_csv("hir_t2.csv", index=False)
    print("Saved: bir_t1.csv and hir_t2.csv")


#t2时刻各主体可以用来共享的资源数量
available_sharing_t2 = {}
for s in range(1, S + 1):  # 遍历情景
    indices = np.where(scenario_array == s)[0]
    available_sharing_t2[s] = {}
    for idx in indices:  # 遍历该情景下的样本
        sid = sample_id_array[idx]
        available_sharing_t2[s][sid] = gir_numpy_t2 + hir_ns_t2[s][sid]


# ------------------ 构造qir_ns_t2：样本下的对外真实需求 ------------------ #
def build_qir_ns_t2(S, scenario_array, sample_id_array, dir_all, hir_ns_t2, gir_numpy_t2):
    qir_ns_t2 = {}
    for s in range(1, S + 1):
        indices = np.where(scenario_array == s)[0]
        qir_ns_t2[s] = {}
        for idx in indices:
            sid = sample_id_array[idx]
            dir_ns = dir_all[idx]
            hir_sample = hir_ns_t2[s][sid]  # shape: (N, R)
            qir_matrix = np.maximum(dir_ns - hir_sample - gir_numpy_t2, 0)
            qir_ns_t2[s][sid] = qir_matrix
    return qir_ns_t2

qir_ns_t2 = build_qir_ns_t2(S, scenario_array, sample_id_array, dir_all, hir_ns_t2, gir_numpy_t2)


# ------------------ 情景概率载入函数 ------------------ #
def get_scenario_prob(day, csv_path="/Sample_data/scenario_probability_Marcov.csv"):
    df = pd.read_csv(csv_path, index_col="Day")
    return df.loc[day].to_numpy()

t = 2   
scenario_prob_t = get_scenario_prob(t)

# ------------------ 模糊集半径 theta_s ------------------ #
theta_s = np.array([3.27, 3.30, 3.37, 3.37, 3.26, 3.55, 3.56, 3.53, 3.47, 3.49, 3.52, 3.53, 3.51, 3.56]) # shape: (14,)



# ====================== 决策变量 ======================
def define_cvxpy_variables() -> tuple[list[cp.Variable], list[cp.Variable], cp.Variable, cp.Variable]:
    """x: (R 个 N*N) 比例矩阵, non-neg;  fai: 同维度 bool;  pai: (S,N_s);  γ: (S,)"""
    x_iir_t2 = [cp.Variable((N, N), nonneg=True, name=f"x_r{r}") for r in range(R)]
    # 替换为线性化的形式：Big-M = 1
    fai_t2 = [cp.Variable((N, N), boolean=True, name=f"fai_r{r}") for r in range(R)]  #16(k)
    pai_t2 = cp.Variable((S, N_s), name="pai_t2")
    gamma_t2 = cp.Variable(S, name="gamma_t2")
    return x_iir_t2, fai_t2, pai_t2, gamma_t2


# ======================  约束构造 ======================
# ------------------ 展平 w_matrix（构造约束2、3、4要用） ------------------ #
def flatten_w_matrix(df_w, R):
    w_broad = np.repeat(df_w.values[:, :, np.newaxis], R, axis=2)  # (14, 18, 6)
    w_flat = w_broad.reshape(14, -1)  # 每行是一个样本中 18×6 的展平向量
    columns = [f"P{i:02d}_R{r+1}" for i in range(N) for r in range(R)]
    w_broad_df = pd.DataFrame(w_flat, index=df_w.index, columns=columns)
    w_matrix = [w_broad_df.iloc[s].values.reshape(N, R) for s in range(S)]
    return w_matrix, w_flat

w_matrix, w_flat = flatten_w_matrix(df_w, R)

# ------------------ 构造共享矩阵 shared_in / shared_out ------------------ #
def build_shared_matrices(
    x_iir_t2: list[cp.Expression],
    available_sharing_t2: np.ndarray,
    scenario_array: np.ndarray,
    sample_id_array: np.ndarray,
) -> tuple[cp.Expression, cp.Expression]:
    shared_in = {}
    shared_out = {}
    for s in range(1,S+1):
        indices = np.where(scenario_array == s)[0]
        shared_in[s] = {}
        shared_out[s] = {}
        for idx in indices:
            sid = sample_id_array[idx]
            available = available_sharing_t2[s][sid]  # (N, R)
            shared_in_r, shared_out_r = [], []
            for r in range(R):
                abs_mat = cp.multiply(x_iir_t2[r], available[:, r][:, None])  # (N,N)
                shared_in_r.append(cp.sum(abs_mat, axis=0))   # 列和
                shared_out_r.append(cp.sum(abs_mat, axis=1))  # 行和
            shared_in[s][sid] = cp.vstack(shared_in_r).T   # shape (N, R)
            shared_out[s][sid] = cp.vstack(shared_out_r).T # shape (N, R)
    return shared_in, shared_out  # 均为 (N,R)


# ------------------ 构造距离矩阵乘以是否共享的总运输距离 ------------------ #
def build_total_transport_cost(fai_t2, distance_matrix: np.ndarray) -> cp.Expression:
    N = distance_matrix.shape[0]
    cost_terms = []
    for r in range(R):
        row_terms = [cp.sum(cp.multiply(fai_t2[r][i, :], distance_matrix[i, :])) for i in range(N)]
        cost_terms.append(cp.hstack(row_terms))  # (N,)
    total_dist = cp.vstack(cost_terms).T   # (N,R)
    return lamda * total_dist              # (N,R)


def build_constraints(
    x_iir_t2, fai_t2, pai_t2, gamma_t2,
    k_ir, w_matrix, w_flat,
    shared_in, shared_out,
    dir_all, hir_ns_t2, gir_numpy_t2,
    total_transport_cost,
    qir_ns_t2, theta_s,
    scenario_array, sample_id_array, scenario_prob_t
):
    
    constraints = []
    S = len(theta_s)
    R, N = len(x_iir_t2), x_iir_t2[0].shape[0]

    # Constraint 1: (16j)
    epsilon = 1e-5  
    M = 10000
    for r in range(R):
        constraints += [x_iir_t2[r] <= M * fai_t2[r]] 
        constraints += [x_iir_t2[r] >= epsilon * fai_t2[r]]
        constraints += [x_iir_t2[r] >= 0, x_iir_t2[r] <= 1]

    # Constraint 2:  (16b)
    for s in range(1, S + 1):
        w_s = w_matrix[s - 1]                   # (N,R)
        indices = np.where(scenario_array == s)[0]
        for idx in indices:
            sid = sample_id_array[idx]
            dir_ns = dir_all[idx]               # (N,R)
            hir_sample = hir_ns_t2[s][sid]
            lhs = -cp.sum(cp.multiply(k_ir * w_s, dir_ns))
            shared_in_c = shared_in[s][sid]
            rhs = -pai_t2[s - 1, sid] + cp.sum(cp.multiply(k_ir * w_s, -hir_sample - gir_numpy_t2 - shared_in_c)) + cp.sum(total_transport_cost)
            constraints += [lhs >= rhs]


    # Constraint 3:  (16c)
    gamma_lb = [float(np.linalg.norm(k_ir.flatten() * w_flat[s - 1], 2)) for s in range(1, S + 1)]
    for s in range(1, S + 1):
        constraints += [gamma_t2[s - 1] >= gamma_lb[s - 1]]

    # # Constraint 4:  (16d)
    for s in range(1, S + 1):
        w_s = w_matrix[s - 1]
        indices = np.where(scenario_array == s)[0]
        for idx in indices:
            sid = sample_id_array[idx]
            shared_in_c = shared_in[s][sid]
            expr = cp.sum(cp.multiply(k_ir * w_s, -shared_in_c))
            rhs  = -pai_t2[s - 1, sid] + expr + cp.sum(total_transport_cost)
            constraints += [rhs <= 0]


    # # Constraint 5: (16e)
    for s in range(1, S + 1):
        indices = np.where(scenario_array == s)[0]
        for idx in indices:
            sid = sample_id_array[idx]
            constraints += [-pai_t2[s - 1, sid] + cp.sum(total_transport_cost) <= 0]


    # # Constraint 6: (16f)
    accum_q = 0
    accum_shared_in = 0
    for s in range(1, S + 1):
        prob = scenario_prob_t[s - 1]
        theta_val = theta_s[s - 1]
        indices = np.where(scenario_array == s)[0]
        q_sum = 0
        count = 0
        for idx in indices:
            sid = sample_id_array[idx]
            q_sum += qir_ns_t2[s][sid]
            count += 1
        q_mean = q_sum / count
        robust_lower_q = np.maximum(q_mean - theta_val, 0)
        accum_q += prob * robust_lower_q
        for idx in indices:
            sid = sample_id_array[idx]
            accum_shared_in += (prob / count) * shared_in[s][sid]
    constraints += [accum_q >= accum_shared_in]


    # # Constraint 7: (16g)
    accum2 = 0
    for s in range(1, S + 1):
        prob = scenario_prob_t[s - 1]
        theta_mat = np.full((N, R), theta_s[s - 1])
        indices = np.where(scenario_array == s)[0]
        for idx in indices:
            sid = sample_id_array[idx]
            hir_sample = hir_ns_t2[s][sid]
            accum2 += (prob / N_s) * (hir_sample + theta_mat)

    total_shared_out_exprs = [shared_out[s][sid] for s in shared_out for sid in shared_out[s]]
    constraints += [accum2 + gir_numpy_t2 >= cp.sum(cp.vstack(total_shared_out_exprs))]


    
    # # Constraint 8: 
    for r in range(R):
        constraints += [cp.diag(x_iir_t2[r]) == 0]
    
    
    # # Constraint 9: 16(h) and 16(i)
    l_ir = [cp.Variable(N, boolean=True, name=f"l_r{r}") for r in range(R)]
    for r in range(R):
        for i in range(N):
            out_ = cp.sum(x_iir_t2[r][i, :]) - x_iir_t2[r][i, i]
            in_  = cp.sum(x_iir_t2[r][:, i]) - x_iir_t2[r][i, i]
            constraints += [
                out_ <= 10 * (1 - l_ir[r][i]), #M=10
                in_  <= 10 * l_ir[r][i]
            ]
   
    return constraints

# ====================== 目标函数 ====================== 
def build_objective(pai_t2, gamma_t2, scenario_prob, theta_s):
    weights_sample = np.repeat(scenario_prob / N_s, N_s)  # len = S*N_s
    objective_section1 = cp.sum(cp.multiply(cp.vec(pai_t2), weights_sample))
    objective_section2 = cp.sum(cp.multiply(gamma_t2, scenario_prob * theta_s))
    return cp.Minimize(objective_section1 + objective_section2), objective_section1, objective_section2

# ====================== 模型求解函数 ====================== #
def solve_dro_ratio_model(
    k_ir, w_matrix, w_flat,
    hir_ns_t2, gir_numpy_t2, available_sharing_t2,
    qir_ns_t2, theta_s, scenario_prob_t,
    distance_matrix
):
    # Step 1: 定义变量
    x_iir_t2, fai_t2, pai_t2, gamma_t2 = define_cvxpy_variables()

    # Step 2: 共享矩阵
    shared_in, shared_out = build_shared_matrices(x_iir_t2, available_sharing_t2, scenario_array, sample_id_array)

    # Step 3: 运输成本
    transport_cost = build_total_transport_cost(fai_t2, distance_matrix)

    # Step 4: 构造约束
    constraints = build_constraints(
        x_iir_t2, fai_t2, pai_t2, gamma_t2,
        k_ir, w_matrix, w_flat,
        shared_in, shared_out,
        dir_all, hir_ns_t2, gir_numpy_t2,
        transport_cost,
        qir_ns_t2, theta_s,
        scenario_array, sample_id_array, scenario_prob_t
    )

    # Step 5: 构造目标函数
    objective,objective_section1,objective_section2 = build_objective(pai_t2, gamma_t2, scenario_prob_t, theta_s)

    # Step 6: 建立模型并求解
    problem = cp.Problem(objective, constraints)
    problem.solve(solver=cp.GUROBI, verbose=True)

    return {
        "problem": problem,
        "x_iir_t2": x_iir_t2,
        "fai_t2": fai_t2,
        "pai_t2": pai_t2,
        "gamma_t2": gamma_t2,
        "objective": objective,
        "objective_section1": objective_section1,
        "objective_section2": objective_section2,
        "transport_cost":  transport_cost, 
        # "shared_in": shared_in.value,         
        # "shared_out": shared_out.value   
    }

bir_hir_csv = save_bir_and_hir_to_csv(
    bir_t1=bir_t1,
    hir_ns_t2=hir_ns_t2,
    N=N,
    R=R,
    scenario_array=scenario_array,
    sample_id_array=sample_id_array
)

# ------------------ 输出一些内容 ------------------ #
result = solve_dro_ratio_model(k_ir, w_matrix, w_flat,
        hir_ns_t2, gir_numpy_t2, available_sharing_t2,
        qir_ns_t2, theta_s, scenario_prob_t,
        distance_df_numpy
    )


print("Objective value:", result["problem"].value)
print("Objective_section1 value:", result["objective_section1"].value)
print("Objective_section2 value:", result["objective_section2"].value)
print("Objective status:", result["problem"].status)

# # -----------------保存结果------------------ ##
# # # ----------- 保存前一天的共享情况（数量） ----------- ##
resource_names = ["r1", "r2", "r3", "r4", "r5", "r6"] #列名
subject_names = [f"主体{i+1}" for i in range(18)] #行名
number_share_in_t1 = pd.DataFrame(shared_in_t1, columns=resource_names, index=subject_names)
number_share_out_t1 = pd.DataFrame(shared_out_t1, columns=resource_names, index=subject_names)
number_share_in_t1.to_csv("s1_number_share_in_t1.csv",index=True) #18个主体总共共享得到的6种资源
number_share_out_t1.to_csv("s1_number_share_out_t1.csv",index=True) #18个主体总共共享出去的6种资源


abs_mat_blocks = np.vstack(abs_mats)  # shape: (R*N, N) = (108, 18)
index_names = [f"R{r+1}_主体{i+1}" for r in range(R) for i in range(18)]# 行名（主体1–18 × r1–r6）
column_names = [f"主体{j+1}" for j in range(18)]
df_abs_mat_all = pd.DataFrame(abs_mat_blocks, index=index_names, columns=column_names)
df_abs_mat_all.to_csv("s1_abs_shared_matrix_all.csv", encoding="utf-8-sig") #18个主体之间针对6种资源共享的数量矩阵