import numpy as np
import pandas as pd

df = pd.read_excel("Normalized_matrix_data/scenario1_data.xlsx")  
demand_levels = ["很低", "较低", "一般", "较高", "很高"]

def calculate_topsis_scores(df):
    result = []
    summary = []
    num_samples = len(df) // 5 

    for i in range(num_samples):
        block = df.iloc[i*5:(i+1)*5, :]  
        block_np = block.to_numpy()

        ideal_best = block_np.max(axis=0)
        ideal_worst = block_np.min(axis=0)
        print("正、负理想解:")
        print(ideal_best)
        print(ideal_worst)
        s_list = []
        for row in block_np:
            d_pos = np.linalg.norm(row - ideal_best)  
            d_neg = np.linalg.norm(row - ideal_worst) 
            # print(d_neg)
            s = d_neg / (d_pos + d_neg)
            s_list.append((d_pos, d_neg, s))
   
        s_values = [item[2] for item in s_list]
        max_index = int(np.argmax(s_values))
        max_s = s_values[max_index]
        level = demand_levels[max_index]
        sample_id = f'Sample_{i+1}'

        for d_pos, d_neg, s in s_list:
            result.append({
                'sample_id': sample_id,
                'd_pos': d_pos,
                'd_neg': d_neg,
                's': s,
            })

        summary.append({
            'sample_id': sample_id,
            '最大贴近度': max_s,
            '最大位置': max_index,
            '判断等级': level
        })

    return pd.DataFrame(result), pd.DataFrame(summary)

scores_df, summary_df = calculate_topsis_scores(df)
print("明细结果(scores_df):")
print(scores_df)
print("\n样本判断汇总(summary_df):")
print(summary_df)
