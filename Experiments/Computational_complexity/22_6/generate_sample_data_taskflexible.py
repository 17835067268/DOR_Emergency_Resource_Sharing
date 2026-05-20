import numpy as np
import pandas as pd

# ====================== 参数设置 ======================
np.random.seed(42) 
N, R = 22, 6        
N_S = 10           
S = 14             

subject_set = ["a1社区居委会","a1社区物业","a2社区居委会","a2社区物业","a3社区居委会","a3社区物业","b1社区居委会","b1社区物业","b2社区居委会","b2社区物业","b3社区居委会","b3社区物业","c1社区居委会","c1社区物业","c2社区居委会","c2社区物业","c3社区居委会","c3社区物业","A街道卫生服务中心","B街道卫生服务中心","C街道卫生服务中心","D区疾控中心"]
scenario_set = ["弱传播_社区内_单点爆发", "弱传播_社区内_多点关联","弱传播_跨社区_多点关联","弱传播_跨街道_多点关联", "稳传播_社区内_单点爆发", "稳传播_社区内_多点关联", "稳传播_跨社区_多点关联", "稳传播_跨街道_多点关联", "强传播_社区内_多点关联", "强传播_社区内_多点散发", "强传播_跨社区_多点关联", "强传播_跨社区_多点散发", "强传播_跨街道_多点关联", "强传播_跨街道_多点散发"]
resource_set = ["医用口罩","防护服","消毒液","护目镜","帐篷","社区卫生服务中心医护人员"]
task_set = ["epidemiological investigation","disinfection","nucleic acid testing","infection or contact transfer","neighborhood entrance screening"] 
tasks_required_resources = {'epidemiological investigation': {'医用口罩', '防护服', '护目镜', '社区卫生服务中心医护人员'},'disinfection':{'医用口罩', '防护服', '消毒液', '护目镜'},'nucleic acid testing':{'医用口罩', '防护服', '护目镜', '帐篷', '社区卫生服务中心医护人员'},'infection or contact transfer':{'医用口罩', '防护服','护目镜','社区卫生服务中心医护人员'},'neighborhood entrance screening': {'医用口罩', '防护服', '护目镜', '帐篷'}}
task_process_subject = {'epidemiological investigation': {'社区居委会', '街道卫生服务中心', '区疾控中心'},'disinfection':{'社区居委会', '社区物业'},'nucleic acid testing':{'街道卫生服务中心'},'infection or contact transfer':{'社区居委会','街道卫生服务中心'},'neighborhood entrance screening': {'社区居委会'}}
infected_neighborhood_task = ["epidemiological investigation","infection or contact transfer","neighborhood entrance screening"]

subject_task_map = {}

for subject in subject_set:
    subject_task_map[subject] = []
    for task, valid_subjects in task_process_subject.items():
        for role in valid_subjects:
            if role in subject:
                subject_task_map[subject].append(task)
                break  

# ====================== 主体映射：主体编号(社区, 街道, 区) ======================
subject_info = {
    0: ("a1", "A", "D"), 1: ("a1", "A", "D"),
    2: ("a2", "A", "D"), 3: ("a2", "A", "D"),
    4: ("a3", "A", "D"), 5: ("a3", "A", "D"),
    6: ("b1", "B", "D"), 7: ("b1", "B", "D"),
    8: ("b2", "B", "D"), 9: ("b2", "B", "D"),
    10: ("b3", "B", "D"), 11: ("b3", "B", "D"),
    12: ("c1", "C", "D"), 13: ("c1", "C", "D"),
    14: ("c2", "C", "D"), 15: ("c2", "C", "D"),
    16: ("c3", "C", "D"), 17: ("c3", "C", "D"),
    18: (None, "A", "D"), 19: (None, "B", "D"), 20: (None, "C", "D"),
    21: (None, None, "D")
}

# ====================== 街道对应社区 ======================
town_to_communities = {
    "A": ["a1", "a2", "a3"],
    "B": ["b1", "b2", "b3"],
    "C": ["c1", "c2", "c3"]
}

# ====================== 各情景下感染社区集合 ======================
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

# ====================== 各情景下各个主体要执行的任务是什么 ======================
def extract_region(subject_name):
    for level_name in ["社区", "街道", "区"]:  
        if level_name in subject_name:  	
            prefix = subject_name.split(level_name)[0] 
            return prefix, level_name
    return None, None

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
                elif level_name == "街道":
                    if region in town_to_communities: 
                        if any(com in infected for com in town_to_communities[region]):
                            executed_tasks.append(task)
                elif level_name == "区": 
                    executed_tasks.append(task)  
            else:
                executed_tasks.append(task) 
        scenario_subject_tasks[s][subject] = executed_tasks

# ====================== 各类主体在不同情景下的需求等级 ======================
demand_levels = ["很低", "较低", "一般", "较高", "很高"]
level_to_index = {v: i for i, v in enumerate(demand_levels)}


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


level_name_to_index = {"很低": 0, "较低": 1, "一般": 2, "较高": 3, "很高": 4}

alpha = {1: 1, 2: 1, 3: 0.5, 4: 1, 5: 0.4, 6: 0.1}
beta = {1: 1.1, 2: 1, 3: 0.5, 4: 1, 5: 0, 6: 0} 

base_mu = np.array([
    [12, 4, 5, 4, 1, 0],  
    [18, 6, 20, 6, 0, 0],
    [12, 4, 5, 4, 1, 0],  
    [18, 6, 20, 6, 0, 0], 
    [12, 4, 5, 4, 1, 0],  
    [18, 6, 20, 6, 0, 0],
    [12, 4, 5, 4, 1, 0],  
    [18, 6, 20, 6, 0, 0],
    [12, 4, 5, 4, 1, 0], 
    [18, 6, 20, 6, 0, 0],
    [12, 4, 5, 4, 1, 0], 
    [18, 6, 20, 6, 0, 0],
    [12, 4, 5, 4, 1, 0],  
    [18, 6, 20, 6, 0, 0],
    [12, 4, 5, 4, 1, 0],  
    [18, 6, 20, 6, 0, 0],
    [12, 4, 5, 4, 1, 0],   
    [18, 6, 20, 6, 0, 0], 
    [24, 8, 0, 8, 0, 8], 
    [18, 6, 0, 6, 0, 6],
    [18, 6, 0, 6, 0, 6],
    [24, 8, 0, 8, 0, 0] 
]) 
max_fluctuations = np.array([
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [2, 1, 1, 1, 0, 0],
    [2, 1, 2, 1, 0, 0],
    [3, 2, 0, 2, 0, 2],
    [3, 2, 0, 2, 0, 2],
    [3, 2, 0, 2, 0, 2],
    [3, 2, 0, 2, 0, 0]
])

base_sigma = np.array(max_fluctuations/3) 


# ====================== 构造资源分布 ======================
resource_params = {}
for j in range(N): #主体
    resource_params[j] = {}
    for k in range(1, R + 1): #资源
        resource_params[j][k] = {}
        for level in demand_levels: 
            idx = level_name_to_index[level] 
            mu = base_mu[j, k - 1] * (1 + alpha[k] * idx) 
            sigma = base_sigma[j, k - 1] * (1 + beta[k] * idx) 
            resource_params[j][k][level] = (mu, sigma)

# ====================== 样本生成（结合样本生成规则） ======================
samples_all, meta_info = [], []

for s in range(1, S + 1):  # 情景编号
    infected = infected_communities[s]
    subject_task_dict = scenario_subject_tasks[s] 
    for sample_id in range(N_S): 
        sample_vector = []

        for j in range(N):  # 主体编号
            subj_name = subject_set[j]
            com, town, dist = subject_info[j]
            subject_tasks = subject_task_dict.get(subj_name, [])

            if com:
                if com in infected: 
                    ctype = 1
                elif any(c in infected for c in town_to_communities[town] if c != com):
                    ctype = 2
                else:
                    ctype = 3
                level_str = level_table[s][ctype]
            elif town:
                if any(c in infected for c in town_to_communities[town]):
                    level_str = level_table[s]['T1']
                else:
                    level_str = level_table[s]['T2']   
            else:
                level_str = level_table[s]['D']

            level_idx = level_name_to_index[level_str]
            final_level = demand_levels[level_idx]

            for k in range(1, R + 1):  
                res_name = resource_set[k-1]

                relevant_tasks = [
                    task for task in subject_tasks 
                    if res_name in tasks_required_resources.get(task, set()) 
                ]

                if relevant_tasks:
                    mu, sigma = resource_params[j][k][final_level]
                    sample = np.random.normal(loc=mu, scale=sigma) 
    
                    sample = max(0, int(round(sample))) 
                else:
                    sample = 0

                sample_vector.append(sample) 

        samples_all.append(sample_vector)
        meta_info.append({'scenario': s, 'sample_id': sample_id})

#====================== 列名构造 ======================
column_names = [f'P{j+1:02d}_R{k}' for j in range(N) for k in range(1, R + 1)]

# ====================== 构造 DataFrame ======================
df_samples = pd.DataFrame(samples_all, columns=column_names)
df_meta = pd.DataFrame(meta_info)
df_combined = pd.concat([df_meta, df_samples], axis=1)

# 保存路径
csv_path = "22_6_simulated_demand_structured_Ns_10.csv" 
df_combined.to_csv(csv_path, index=False)
print(f"文件已保存为：{csv_path}")





