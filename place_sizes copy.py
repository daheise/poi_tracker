from json import tool
from statistics import median
import pandas
import numpy as np
import math
from scipy import stats


df = pandas.read_csv("data/2021_Gaz_place_national.txt", delimiter="\t")
pois = pandas.read_csv("data/msfs_pois.csv")
pois = pois[(pois["Type"] == "Settlement")]

df = df[(df["NAME"].str.contains("|".join(pois["Name"])))]
# df = df[['NAME' in x for x in pois['Name']]]
df = df[(df["ALAND_SQMI"] > 1.4142)]
total_area = df["ALAND_SQMI"] + df["AWATER_SQMI"]
print(total_area.head(5))
print(total_area.describe())
total_area = total_area[(np.abs(stats.zscore(total_area)) < 3)]
print(total_area.head(5))
print(total_area.describe())

mean = total_area.mean()
median = total_area.median()
quantiles = total_area.quantile(q=np.arange(0, 1, 0.01))
max = total_area.max()
max_diagonal = math.sqrt(max) * math.sqrt(2) / 2
mean_diagonal = math.sqrt(mean) * math.sqrt(2) / 2
median_diagonal = math.sqrt(median) * math.sqrt(2) / 2
for q in quantiles:
    print(math.sqrt(q) * math.sqrt(2) / 2)

pass
