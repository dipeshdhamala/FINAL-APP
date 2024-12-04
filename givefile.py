#givefile
kf = k * np.exp(-beta * 96485 * (voltage-U) / (1000*8.314 * T))
kb = k * np.exp((1-beta) * 96485 * (voltage-U) / (1000*8.314 * T))
area=1
n=1
F= 96485
line("func1", ["i_conc_a = n * F * area * kb * conc", "i_conc_c = -n * F * area * kf * conc","i_total=i_conc_a+i_conc_c"], "voltage", "Rate of reaction")
sliderupdate("func1","k",-11,0,-4,0.001)
sliderupdate("func1","T",50,2000,373,25)
sliderupdate("func1","U",-1000,1000,0,5)
sliderupdate("func1","beta",0,1,0.5,0.0001)
sliderupdate("func1","x_range_line",-1000,1000,[-250,250],50)
line("func2", ["kf = k * np.exp(-beta * 96485 * (voltage-U) / (1000*8.314 * T))", "kb = k * np.exp((1-beta) * 96485 * (voltage-U) / (1000*8.314 * T))"], "voltage", "Rate constant")
sliderupdate("func2","k",-11,0,-4,0.001)
sliderupdate("func2","T",50,2000,373,25)
sliderupdate("func2","beta",0,1,0.5,0.01)
sliderupdate("func2","x_range_line",-1000,1000,[-250,250],50,"value of voltage")
sliderupdate("func2","U",-1000,1000,0,5,"value of U")

