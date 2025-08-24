import pandas as pd

input_path = "youtube/input.xlsx"
output_path1 = "youtube/output1.xlsx"
output_path2 = "youtube/output2.xlsx"

def create_bulk_data():
    df = pd.read_excel(input_path, sheet_name="Sheet1")
    
    row_count = df.shape[0]
    df1 = pd.DataFrame([[None]*2 for _ in range(row_count * 2)])
    df2 = pd.DataFrame([[None]*2 for _ in range(row_count * 2)])
    
    for i in range(row_count * 2):
        if i % 2 == 0:
            df1.iloc[i, 0] = "O:" + df.iloc[i // 2, 0]
            df2.iloc[i, 0] = df.iloc[i // 2, 0]
        else:
            df1.iloc[i, 0] = "X:" + df.iloc[i // 2, 1]
            df2.iloc[i, 1] = df.iloc[i // 2, 1]
    
    df1.to_excel(output_path1, index=False, header=False)
    df2.to_excel(output_path2, index=False, header=False)
