# -*- coding: utf-8 -*-


import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import find_peaks_cwt


bimodal = [
    1478, 2640, 2364, 2611, 1458, 2556, 1526, 1448, 2664, 1449,
    1472, 2830, 2597, 2588, 2464, 1467, 1430, 1503, 2706, 2501,
    2537, 2601, 2622, 1363, 1420, 1553, 2500, 1406, 1401, 1511,
    1366, 1360, 1406, 1426, 2297, 1257, 2260, 1266, 1270, 1242,
    2270, 2241, 1172, 2240, 1252, 1260, 2245, 2234, 1306, 1168,
    2211, 1200, 2149, 1505, 1172, 1308, 1531, 1295, 1252, 1146,
    2176, 1246, 2266, 1158, 1177, 2259, 2201, 1171, 1209, 2095,
    1166, 2149, 2291, 1360, 1163, 2228, 1263, 1199, 2203, 2225,
    1243, 2214, 1226, 2450, 2187, 2232, 1222, 1197, 1256, 1254,
    1274, 1244, 1265, 1216, 2239, 2262, 2246, 1296, 2269, 1277,
    1223, 1331, 2383, 1211, 1326, 2300, 1346, 2312, 1323, 1290,
    1229, 1292, 1213, 1325, 1341, 1226, 1315, 1242, 1202, 2309,
    2251, 2342, 1215, 1315, 1279, 1282, 1322, 1473, 1321, 1337,
    1305, 1239, 1215, 1286, 1273, 1382, 2328, 2315, 1261, 1241,
    2278, 2297, 2151, 2243, 2215, 2175, 2285, 2416, 2441, 2280,
    2458, 2349, 2347, 2379, 1299, 2273, 2399, 2239, 2353, 2379,
    2367, 1261, 2388, 2411, 2368, 2408, 2383, 2342, 1256, 2474,
    2263, 2327, 2385, 2400, 2374, 2436, 2374, 2483, 2373, 2391,
    2417, 2427, 2364, 2499, 2447, 2370, 2446, 2423, 2392, 2278,
    2472, 2406, 2432, 2631, 2392, 2510, 2484, 2495, 2453, 2428,
    2359, 2470, 2494, 2416, 2416, 2431, 2407, 2372, 2298, 2422,
    2396, 2351, 2462, 2333, 2455, 2449, 2438, 2398, 2414, 2359,
    2417, 2443, 2353, 2382, 2501, 2420, 2389, 2464, 2411, 2402,
    2438, 2458, 2329, 2375, 2367, 2428, 2434, 2491, 2329, 2447,
    2425, 2394, 2348, 2361, 2411, 2399, 2408, 2454, 2211, 2215,
    2387, 2178, 1288, 1211, 1265, 2361, 2275, 1197, 1241, 2317,
    1309, 2368, 1190, 1245, 2340, 1264, 2395, 2326, 2260, 2347,
    1341, 1202, 1367, 2283, 2419, 2411, 2291, 2289, 2269, 2321,
    1246, 1220, 1301, 2345, 2208, 2360, 2385, 1201, 2281, 1235,
    1243, 1265, 1262, 1273, 2342, 2259, 2312, 1192, 1391, 1259,
    1226, 1283, 2289, 1359, 1442, 2528, 2397, 2376, 2350, 1313,
    2322, 2291, 2241, 2273, 2291, 1231, 1220, 2272, 2328, 2418,
    2435, 1278, 2444, 2341, 2332, 2298, 2316, 2398, 1198, 2393,
    1289, 1241, 1170, 1336, 1255, 2360, 2287, 1240, 2260, 1323,
    1231, 1272, 1183, 2285, 2258, 2307, 2307, 2165, 2406, 2295,
    1234, 1189, 1186, 2320, 2312, 2400, 2321, 1170, 2318, 1209,
    1270, 2374, 2299, 1206, 1225, 2329, 2324, 1248, 2346, 2285,
    2247
]

bimodal_np = np.asarray(bimodal)

# Find the peaks
bimodal_hist, edges = np.histogram(bimodal, bins=50)
peaks = find_peaks_cwt(bimodal_hist, np.arange(1,60), min_length=10); peaks

# Determine multi-modal areas
zero_inds = np.where(bimodal_hist == 0)[0]; zero_inds
hists = []
for peakind in peaks:
    start_ind = 0
    end_ind = 0

    for count, ind in enumerate(zero_inds):
        if peakind >= ind:
            continue
        else:
            end_ind = ind
            if count - 1 >= 0:
                start_ind = zero_inds[count-1]
            break

    hists.append((start_ind, end_ind))
hists

# Plot histogram with multi-modal areas found (within the red bars)
plt.figure()
plt.plot(edges[:-1], bimodal_hist)

for start, end in hists:
    plt.axvline(edges[start], color='r')
    plt.axvline(edges[end], color='r')

plt.title("Bi-modal values as histogram in blue, peak areas found in red")
plt.ylabel("Count")
plt.xlabel("Bi-modal data values")

plt.scatter(bimodal_np, list(range(len(bimodal_np))))

# Get data from each mode
bimodal_data_one = bimodal_np.copy()
bimodal_data_one[
        np.asarray(list(
            set(list(np.where(bimodal_np <= edges[hists[0][0]]))[0]) | \
            set(list(np.where(bimodal_np >= edges[hists[0][1]]))[0])
        ))
] = 0

bimodal_data_two = bimodal_np.copy()
bimodal_data_two[
        np.asarray(list(
            set(list(np.where(bimodal_np <= edges[hists[1][0]]))[0]) | \
            set(list(np.where(bimodal_np >= edges[hists[1][1]]))[0])
        ))
] = 0

# Show the split bimodal data
plt.figure()
plt.scatter(list(range(len(bimodal_np))), bimodal_data_one)

plt.figure()
plt.scatter(list(range(len(bimodal_np))), bimodal_data_two)

# Get %-change of all modes
nz_inds = np.nonzero(bimodal_data_one)
bimodal_data_one_pc = np.asarray([float(v) for v in bimodal_data_one.copy()])
bimodal_data_one_pc[nz_inds] = (bimodal_data_one[nz_inds] - np.mean(bimodal_data_one[nz_inds])) / \
    np.mean(bimodal_data_one[nz_inds])

plt.figure()
plt.scatter(list(range(len(bimodal_np))), bimodal_data_one_pc)

nz_inds = np.nonzero(bimodal_data_two)
bimodal_data_two_pc = np.asarray([float(v) for v in bimodal_data_two.copy()])
bimodal_data_two_pc[nz_inds] = (bimodal_data_two[nz_inds] - np.mean(bimodal_data_two[nz_inds])) / \
    np.mean(bimodal_data_two[nz_inds])

plt.figure()
plt.scatter(list(range(len(bimodal_np))), bimodal_data_two_pc)

# Join all the modes together as a corrected time series
bimodal_corrected = (bimodal_data_one_pc + bimodal_data_two_pc) * 100

# Plot corrected data
plt.figure()
plt.scatter(list(range(len(bimodal_np))), bimodal_corrected * 100)
plt.title("Bimodal corrected data")
plt.xlabel("Time")
plt.ylabel("%-Change from mean")

# Plot corrected data versus original data
plt.figure(); plt.subplot(1,2,1);
plt.scatter(list(range(len(bimodal_np))), bimodal_np)
for start, end in hists:
    plt.axhline(edges[start], color='r')
    plt.axhline(edges[end], color='r')
plt.title("Original data")
plt.xlabel("Time")
plt.ylabel("Data units (a.u.)")

plt.subplot(1,2,2);
plt.scatter(list(range(len(bimodal_np))), bimodal_corrected)
plt.title("Bimodal corrected data")
plt.xlabel("Time")
plt.ylabel("%-Change from mean")

# Plot original histogram versus corrected histogram
plt.figure()
plt.subplot(1,2,1)
plt.plot(edges[:-1], bimodal_hist)
for start, end in hists:
    plt.axvline(edges[start], color='r')
    plt.axvline(edges[end], color='r')
plt.title("Bi-modal values as histogram in blue, peak areas found in red")
plt.ylabel("Count")
plt.xlabel("Bi-modal data values")

plt.subplot(1,2,2)
newhist, newedges = np.histogram(bimodal_corrected, bins=30)
plt.plot(newedges[:-1], newhist)
plt.title("Corrected bi-modal values as histogram")
plt.xlabel("%-Change values")
plt.ylabel("Count")

# Plot stddevs and means for uncorrected vs corrected
plt.figure(); plt.subplot(1,2,1);
plt.scatter(list(range(len(bimodal_np))), bimodal_np)
for start, end in hists:
    plt.axhline(edges[start], color='r')
    plt.axhline(edges[end], color='r')
plt.title("Original data")
plt.xlabel("Time")
plt.ylabel("Data units (a.u.)")

means = np.zeros(len(bimodal_np))
ranges = np.zeros(len(bimodal_np))
stddevs = np.zeros(len(bimodal_np))
binsize = 15
for i in range(int(len(bimodal_np)/binsize)+1):
    if i*binsize >= len(bimodal_np):
        continue
    arang = (i*binsize, (i*binsize)+binsize)
    pts = bimodal_np[arang[0]:arang[1]]
    means[arang[0]:arang[1]] = np.mean(pts)
    stddevs[arang[0]:arang[1]] = np.std(pts)

plt.plot(means, color='black')
plt.fill_between(np.arange(len(bimodal_np)), means-stddevs, means+stddevs, alpha=0.3)

plt.subplot(1,2,2);
plt.scatter(list(range(len(bimodal_np))), bimodal_corrected)
plt.title("Bimodal corrected data")
plt.xlabel("Time")
plt.ylabel("%-Change from mean")

means = np.zeros(len(bimodal_corrected))
ranges = np.zeros(len(bimodal_corrected))
stddevs = np.zeros(len(bimodal_corrected))
binsize = 15
for i in range(int(len(bimodal_corrected)/binsize)+1):
    if i*binsize >= len(bimodal_corrected):
        continue
    arang = (i*binsize, (i*binsize)+binsize)
    pts = bimodal_corrected[arang[0]:arang[1]]
    means[arang[0]:arang[1]] = np.mean(pts)
    stddevs[arang[0]:arang[1]] = np.std(pts)

plt.plot(means, color='black')
plt.fill_between(np.arange(len(bimodal_corrected)), means-stddevs, means+stddevs, alpha=0.3)



