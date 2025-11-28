import numpy as np
import pandas as pd

arr = np.load("data_output/bend_230.npy", allow_pickle=True)
print(arr.item())

"Output Format: [x, y, z, u, v, w, p, y_wall, is_fluid, is_wall, is_inlet, is_outlet]"
#                0  1  2  3  4  5  6    7         8        9        10         11

print("done")
