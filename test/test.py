import math
import trueskill
import numpy as np
import matplotlib.pyplot as plt


x = np.linspace(-6, 6, 100)

# arr = []
# for i in x:
#     arr.append(trueskill.gaussian_at(i))
# plt.plot(x, arr)
# # plt.show()

# arr = []
# for i in x:
#     arr.append(trueskill.gaussian_at(i, 2, 3))
# plt.plot(x, arr)
# plt.show()


# arr = []
# for i in x:
#     arr.append(trueskill.gaussian_cumulative_to(i))
# plt.plot(x, arr)
# # plt.show()

# arr = []
# for i in x:
#     arr.append(trueskill.gaussian_cumulative_to(i, 2, 3))
# plt.plot(x, arr)
# plt.show()

# # V within --looks good
# arr = []
# for i in x:
#     arr.append(trueskill.v_within_margin(i, 0.5))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.v_within_margin(i, 1.))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.v_within_margin(i, 4.))
# plt.plot(x, arr)
# plt.show()

# V exceeds -- Some strange dip --fiddled with cutoffs
# arr = []
# for i in x:
#     arr.append(trueskill.v_exceeds_margin(i, 0.5))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.v_exceeds_margin(i, 1.))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.v_exceeds_margin(i, 4.))
# plt.plot(x, arr)
# plt.show()

# w exceeds -- Some strange dip
# arr = []
# for i in x:
#     arr.append(trueskill.w_exceeds_margin(i, 0.5))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.w_exceeds_margin(i, 1.))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.w_exceeds_margin(i, 4.))
# plt.plot(x, arr)
# plt.show()

# w less -- looks good
# arr = []
# for i in x:
#     arr.append(trueskill.w_within_margin(i, 0.5))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.w_within_margin(i, 1.))
# plt.plot(x, arr)
# arr = []
# for i in x:
#     arr.append(trueskill.w_within_margin(i, 4.))
# plt.plot(x, arr)
# plt.show()