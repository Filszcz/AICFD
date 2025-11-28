import numpy as np
import pandas as pd

arr = np.load("data_output/straight_3.npz")
print(arr.shape)

"Output Format: [x, y, z, u, v, w, p, y_wall, is_fluid, is_wall, is_inlet, is_outlet]"
#                0  1  2  3  4  5  6    7         8        9        10         11

# for i in range(5000):
#     print(arr[i, 7])

pd1 = pd.DataFrame(arr)

print(pd1)
print("done")
