# ========================== givefile.py ==========================
# This file contains configuration commands for plotting a dynamic Butler-Volmer visualization.
# It defines variable assignments, plotting instructions, and slider behavior.

# ---------- VARIABLE DEFINITIONS ----------
# Define forward rate constant expression using the Butler-Volmer equation
kf = k * np.exp(-beta * F * (voltage - U) / (1000 * 8.314 * T))

# Define backward rate constant using the complementary expression
kb = k * np.exp((1 - beta) * 96485 * (voltage - U) / (1000 * 8.314 * T))

# Set fixed constants
area = 1        
n = 1           
F = 96485       
# ---------- DEFINE A PLOT BLOCK ----------
# The `line(...)` command defines a new plot component named "func1".
# It has two function lists:
# - func_list1: actual current equations to evaluate and plot
# - func_list2: contains display versions or simplified names of key equations like kb and kf
# The last two arguments specify the x-axis and y-axis labels respectively.
line("func1", ["i_conc_a = n * F * area * kb * conc", "i_conc_c = -n *F * area * kf * conc","i_total=i_conc_a+i_conc_c"],["kf=kf","kb=kb"] ,"voltage", "Rate of reaction")
# ---------- SLIDER DEFINITIONS ----------
# These commands attach sliders to the "func1" plot.
# Each slider allows the user to interactively change one variable in real time.

# Slider for `k`: rate constant coefficient
sliderupdate("func1", "k", -11, 0, -4, 0.001)

# Slider for `T`: temperature in Kelvin
sliderupdate("func1", "T", 50, 2000, 373, 25)

# Slider for `U`: standard electrode potential in mV
sliderupdate("func1", "U", -1000, 1000, 0, 5)

# Slider for `beta`: symmetry factor (usually between 0 and 1)
sliderupdate("func1", "beta", 0, 1, 0.5, 0.0001)

sliderupdate("func1", "conc", 0, 2, 0.5, 0.0001)

# Slider to control the X-axis range for the voltage plot in mV
# Allows zooming and panning across different voltage values
sliderupdate("func1", "x_range_line", -1000, 1000, [-250, 250], 50, "voltage")
