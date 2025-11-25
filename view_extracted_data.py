import numpy as np
import pandas as pd

arr = np.load("extracted_data/sim_L3.00_D0.25_U0.25_Ref1.npy")
print(arr.shape)

for i in range(1000):
    print(arr[i,11])

print("done")
