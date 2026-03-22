import xarray as xr
import os
import matplotlib.pyplot as plt

data_folder = "nices_datasets"

values = []
count = 0

for root, dirs, files in os.walk(data_folder):

    for file in files:

        if ".nc" in file:   # detect netcdf files

            path = os.path.join(root, file)

            print("Reading:", path)

            ds = xr.open_dataset(path)

            vapour = ds["water_vapor_profile"].mean().values

            values.append(float(vapour))

            count += 1

print("Total files processed:", count)

if len(values) > 0:

    plt.figure(figsize=(10,5))
    plt.plot(values)

    plt.title("Water Vapour Trend (Jan–Mar 2023)")
    plt.xlabel("Days")
    plt.ylabel("Average Vapour")

    plt.show()

else:
    print("No data found")