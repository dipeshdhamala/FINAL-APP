This code is a web app written in Shiny Python that displays the current plot and reaction rate for the anode and cathode. this is the link for the web app: https://dipeshapp.shinyapps.io/final_app/
In the give file using line command you can use it to form line plot of different equation . For example : line("func1", ["i_conc_a = n * F * area * kb * conc", "i_conc_c = -n * F * area * kf * conc","i_total=i_conc_a+i_conc_c"], "voltage", "Rate of reaction")
Here, first we havae to declare the function name as func1 in example then equation for the plot and x-axis and y- axis
another function is "sliderupdate" which is used to manipulated the slider for the variable in the equation: for example : sliderupdate("func1","k",-11,0,-4,0.001)
here first is in which function you want to operate second is variable name and third and fourth is upper and lower limit of the slider and fifth is initialization of slider and last one is the increament of the slider 
