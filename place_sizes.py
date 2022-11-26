from statistics import median
import pandas
import numpy as np
import math
from scipy import stats


df = pandas.read_csv("data/2021_Gaz_place_national.txt", delimiter="\t")
df = df[df["NAME"].str.contains("city")]
total_area = df["ALAND_SQMI"] + df["AWATER_SQMI"]
print(total_area.describe())
Q1 = total_area.quantile(0.25)
Q3 = total_area.quantile(0.75)
IQR = Q3 - Q1
lower_lim = Q1 - 2 * IQR
upper_lim = Q3 + 2 * IQR
lower_outliers = total_area < lower_lim
upper_outliers = total_area > upper_lim
# total_area[(lower_outliers | upper_outliers)]
# total_area = total_area[~(lower_outliers | upper_outliers)]
mean = total_area.mean()
median = total_area.median()
quantiles = total_area.quantile(q=np.arange(0, 1, 0.01))
max = total_area.max()
max_diagonal = math.sqrt(max) * math.sqrt(2) / 2
mean_diagonal = math.sqrt(mean) * math.sqrt(2) / 2
median_diagonal = math.sqrt(median) * math.sqrt(2) / 2
for q in quantiles:
    print(math.sqrt(q) * math.sqrt(2) / 2)

max_diagonal = math.sqrt(max / math.pi)
mean_diagonal = math.sqrt(mean / math.pi)
median_diagonal = math.sqrt(median / math.pi)
for q in quantiles:
    print(math.sqrt(q / math.pi))

pass
