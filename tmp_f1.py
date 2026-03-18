import pandas as pd
df = pd.read_csv(r'c:\Users\cresp\OneDrive\Desktop\Dandelion\Collaboration Station\AccuSleePy Demo\AccuSleePy_Demo\outputs\validation_summary.csv')
print("mean_f1:")
print(df[['wake_f1', 'nrem_f1', 'rem_f1']].mean())
print("std_f1:")
print(df[['wake_f1', 'nrem_f1', 'rem_f1']].std())
