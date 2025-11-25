import numpy as np
import pandas as pd

arr = np.load("extracted_data/sim_L3.00_D0.25_U0.25_Ref0.npy")
print(arr.shape)

"Output Format: [x, y, z, u, v, w, p, y_wall, is_fluid, is_wall, is_inlet, is_outlet]"
# print wall distance
for i in range(1000):
    print(arr[i,7])

print("done")
