## Demand-Level Scoring Rules

This folder provides the BWM-TOPSIS procedure used to determine the overall resource demand level of six types units(C1-C6) under 14 scenarios. The core idea is to evaluate how well a given scenario matches five demand-related fators and then convert the evaluation results into a demand level.

### 1. Evaluation dimensions

Each scenario is assessed from five dimensions:

- **Spatial extent**: the geographical scope of epidemic spread.
- **Impact severity**: the potential intensity of the scenario’s impact on grassroots emergency operations.
- **Response urgency**: the time pressure and immediacy of required emergency response.
- **Controllability**: the degree to which the scenario can be effectively controlled through available measures.
- **Response complexity**: the complexity of organizing tasks, actors, and resources under the scenario.

Among these dimensions, spatial extent, impact severity, response urgency, and response complexity are treated as **positive indicators**, meaning that a higher value indicates a higher resource demand level. Controllability is treated as a **negative indicator**, meaning that lower controllability corresponds to higher resource demand.

### 2. Demand levels defination

The resource demand level is divided into five ordered categories:

| Level | Abbreviation | Description |
|---|---|---|
| 1 | VL | Very low |
| 2 | L | Low |
| 3 | M | Medium |
| 4 | H | High |
| 5 | VH | Very high |

For each scenario, the five evaluation dimensions are compared with the five candidate demand levels. The matching degree between each dimension and each candidate level is scored using a five-point scale.

### 3. Matching-degree scores

The matching degree is scored from 1 to 5:

| Score | Meaning |
|---|---|
| 1 | Basically mismatched |
| 2 | Relatively mismatched |
| 3 | Moderately matched |
| 4 | Relatively matched |
| 5 | Highly matched |

A higher score means that the corresponding scenario dimension is more consistent with the candidate demand level. For example, if a scenario has a very limited spatial extent, it is more likely to receive a higher matching score under the VL or L demand levels. If a scenario has a broad spatial extent, high impact severity, high response urgency, low controllability, and high response complexity, it is more likely to receive higher matching scores under the H or VH demand levels.

### 4. Scenario-specific scoring matrix

For each epidemic scenario (initial state is s1), a scoring matrix is constructed. The rows correspond to the five evaluation dimensions, and the columns correspond to the five candidate demand levels, namely VL, L, M, H, and VH.

In addition, scenarios are evaluated for different graaaroots unit types, such as `C1`, `C2`, and `C3`. Therefore, each scenario have multiple scoring matrices, one for graaaroots unit type. 

The general structure of the scoring table is as follows:

| Scenario | Dimension | VL | L | M | H | VH |
|---|---|---:|---:|---:|---:|---:|
| Scenario \(s\) | Spatial extent | score | score | score | score | score |
| Scenario \(s\) | Impact severity | score | score | score | score | score |
| Scenario \(s\) | Response urgency | score | score | score | score | score |
| Scenario \(s\) | Controllability | score | score | score | score | score |
| Scenario \(s\) | Response complexity | score | score | score | score | score |

### 5. BWM-TOPSIS-based demand-level evaluation

After the scoring matrix is obtained, BWM-TOPSIS is used to identify the most appropriate overall demand level for each unit type under each scenario. The procedure is as follows:

(1) Construct the scoring matrix. The scoring matrix is constructed according to the five evaluation dimensions and the five candidate demand levels, namely VL, L, M, H, and VH.

(2) Determine factor weights using BWM Solver. The optimal weights of the five evaluation factors are determined using a publicly available BWM Solver. The scoring matrices and the corresponding optimal weights are stored in the `Score_Weight/` folder.

(3) Normalize the scoring matrix. The normalized matrices are stored in the `Normalized_matrix_data/` folder.

(4) Calculate the overall demand level using TOPSIS. Run `topsis_calculate.py` to identify the final overall demand level for each unit type under each scenario.

