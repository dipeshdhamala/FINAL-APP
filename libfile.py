# ====================== IMPORT REQUIRED LIBRARIES ======================

import re  # For extracting variable names from expressions using regex
from shiny import ui, module, reactive, render  # Core Shiny functions for UI and reactivity
import pandas as pd  # To handle data if needed (not used in this snippet directly)
import numpy as np  # For numerical operations like linspace and arrays
from bokeh.plotting import figure  # For creating interactive plots using Bokeh
from shinywidgets import output_widget, bokeh_dependency, render_bokeh  # Shiny Bokeh integration
from bokeh.palettes import Category10  # Bokeh color palette with distinct line colors
# For 3D and scatter plots using Plotly
import plotly.graph_objects as go
import plotly.io as pio

# ====================== GLOBAL DICTIONARY FOR SLIDER STATE ======================

# Used to store the default values of all sliders so we can reset them later
slider_values = {}

# ====================== UTILITY FUNCTION: EXTRACT VARIABLES FROM EXPRESSIONS ======================

# This function identifies all variable names from the RHS of an expression string
# - It filters out common math functions and already defined variables (e.g., x_label, np)
# - Returns a sorted list of remaining variables, which will be used to create sliders
def extract_parameters(expression, defined_vars, x_label):
    param_pattern = re.compile(r'([a-zA-Z]\w*)')  # Pattern to extract valid variable names
    matches = param_pattern.findall(expression)  # Extract all words that look like variables
    excluded = ['np', 'sin', 'cos', 'tan', 'log', 'exp', 'sqrt']  # Known non-variable math keywords
    return sorted([
        match for match in matches
        if match != x_label and match not in excluded and match not in defined_vars
    ])

# ====================== LINE PLOT UI MODULE ======================

# This UI module dynamically creates sliders for all unique variables used in func_list1 and func_list2,
# and generates placeholders for two separate Bokeh plots (one for each list of equations).
@module.ui
def line_ui(func_list1, func_list2, x_label, y_label):
    defined_vars = set([x_label])  # Start with x_label as already defined

    # ---------- Extract all parameters used in func_list1 ----------
    params1 = set()
    for func in func_list1:
        _, expression = func.split('=')
        params1.update(extract_parameters(expression, defined_vars, x_label))
        lhs_var = func.split('=')[0].strip()  # Extract LHS variable name
        defined_vars.add(lhs_var)  # Add it to defined variables to avoid creating sliders for them

    # ---------- Extract all parameters used in func_list2 ----------
    params2 = set()
    for func in func_list2:
        _, expression = func.split('=')
        params2.update(extract_parameters(expression, defined_vars, x_label))
        lhs_var = func.split('=')[0].strip()
        defined_vars.add(lhs_var)

    # Merge both parameter sets to get all unique variables
    all_params = sorted(params1.union(params2))

    # ---------- Create sliders dynamically for each parameter ----------
    sliders = [
        ui.input_slider(f"{param}", f"Select value for {param}:", min=-10, max=10, value=1)
        for param in all_params
    ]

    # Return complete UI layout with sidebar (sliders) and main panel (2 plots)
    return ui.page_fluid(
        ui.div(
            ui.card(
                ui.card_header("BV Current Plots"),  # Title shown at the top of the card
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_slider("x_range_line", f"Select range for {x_label}:", min=-100, max=100, value=[-10, 10]),
                        *sliders,  # All dynamically generated sliders
                        ui.input_action_button("reset_line", "RESET", class_="btn-primary"),
                        width="40%",  # Sidebar width
                        open="closed"  # Start in collapsed state
                    ),
                    bokeh_dependency(),  # Inject Bokeh's JS/CSS dependencies
                    output_widget("plot_line1"),  # Output area for first plot (func_list1)
                    output_widget("plot_line2")   # Output area for second plot (func_list2)
                ),
                height="900px",  # Card height
                fill=False
            ),
            style="width: 900px;"  # Card width
        )
    )

# ====================== LINE PLOT SERVER MODULE ======================

# This server module listens to user inputs from the UI and renders Bokeh plots accordingly.
# It also supports dynamic slider creation via the external `sliderupdate` function.
@module.server
def line_server(input, output, session, func_list1, func_list2, x_label="x", y_label="y"):
    all_funcs = func_list1 + func_list2  # Combine both function lists for analysis if needed

    # ---------- SLIDERUPDATE: Allow external modules to update any slider ----------
    def sliderupdate(slider_name, min_val, max_val, default_val, step=None, label=None):
        # Store the current default value
        slider_values[slider_name] = default_val

        # If label not given, use variable name
        if label is None:
            label = slider_name

        # If step size not given, calculate a reasonable default
        if step is None:
            step = abs((max_val + min_val) / 100)

        # Send update command to frontend
        session.send_input_message(slider_name, {
            "label": label,
            "min": min_val,
            "max": max_val,
            "value": default_val,
            "step": step
        })

    # ---------- Extract all parameters for both function lists ----------
    defined_vars = set([x_label])
    params1 = set()
    for func in func_list1:
        _, expression = func.split('=')
        params1.update(extract_parameters(expression, defined_vars, x_label))
        lhs_var = func.split('=')[0].strip()
        defined_vars.add(lhs_var)

    params2 = set()
    for func in func_list2:
        _, expression = func.split('=')
        params2.update(extract_parameters(expression, defined_vars, x_label))
        lhs_var = func.split('=')[0].strip()
        defined_vars.add(lhs_var)

    all_params = sorted(params1.union(params2))  # Full list of unique parameters

    # ---------- Reactive Reset Handler ----------
    # Listens for the reset button and restores all sliders to their stored default values
    @reactive.effect
    @reactive.event(input.reset_line)
    def _():
        for param in all_params:
            ui.update_slider(param, value=slider_values.get(param, 1))
        ui.update_slider("x_range_line", value=slider_values.get("x_range_line", [-10, 10]))

    # ====================== PLOT 1: func_list1 ======================
    @render_bokeh
    def plot_line1():
        x_range = input.x_range_line() if input.x_range_line is not None else [-10, 10]
        funcs1 = func_list1[:]

        # Recompute parameters for func_list1 (in case they changed)
        params1.clear()
        defined_vars = set([x_label])
        for func in funcs1:
            _, expression = func.split('=')
            params1.update(extract_parameters(expression, defined_vars, x_label))
            defined_vars.add(func.split('=')[0].strip())

        param_values1 = {param: input[f"{param}"]() for param in params1}  # Get current slider values

        try:
            x = np.linspace(x_range[0], x_range[1], 50)
            context = {x_label: x, "np": np}  # Safe evaluation context
            context.update(param_values1)

            fig = figure(title='Line Plot for Current Vs Voltage',
                         x_axis_label=x_label, y_axis_label="Current",
                         width=100, height=100)

            colors = Category10[10]  # Get 10 distinct colors for plotting

            # Plot each function line from func_list1
            for i, item in enumerate(funcs1):
                try:
                    label, expression = item.split('=', 1)
                    label = label.strip()
                    context[label] = eval(expression, context)  # Evaluate expression
                    y = context[label]
                    fig.line(x, y, line_width=2, legend_label=label, color=colors[i % len(colors)])
                except Exception as e:
                    fig.text(x=0, y=0, text=[f"Error in '{item}': {e}"])
            return fig
        except Exception as e:
            # If there's a global error, return fallback text plot
            fig = figure()
            fig.text(x=0, y=0, text=[f"Error: {e}"])
            return fig

    # ====================== PLOT 2: func_list2 ======================
    @render_bokeh
    def plot_line2():
        x_range = input.x_range_line() if input.x_range_line is not None else [-10, 10]
        funcs2 = func_list2[:]

        # Recompute parameters for func_list2
        params2.clear()
        defined_vars = set([x_label])
        for func in funcs2:
            _, expression = func.split('=')
            params2.update(extract_parameters(expression, defined_vars, x_label))
            defined_vars.add(func.split('=')[0].strip())

        param_values2 = {param: input[f"{param}"]() for param in params2}

        try:
            x = np.linspace(x_range[0], x_range[1], 50)
            context = {x_label: x, "np": np}
            context.update(param_values2)

            fig = figure(title='Line Plot for Reaction Rates Vs Voltage',
                         x_axis_label=x_label, y_axis_label="Reaction Rates",
                         width=100, height=100)

            colors = Category10[10]

            for i, item in enumerate(funcs2):
                try:
                    label, expression = item.split('=', 1)
                    label = label.strip()
                    context[label] = eval(expression, context)
                    y = context[label]
                    fig.line(x, y, line_width=2, legend_label=label, color=colors[i % len(colors)])
                except Exception as e:
                    fig.text(x=0, y=0, text=[f"Error in '{item}': {e}"])
            return fig
        except Exception as e:
            fig = figure()
            fig.text(x=0, y=0, text=[f"Error: {e}"])
            return fig

    # Expose the slider update function for dynamic control from other modules
    return {
        "sliderupdate": sliderupdate
    }

    

# ====================== 3D PLOT UI MODULE ======================
# This module defines the user interface for the 3D plot.
# It includes sliders for selecting the input range of the x and y axes.
@module.ui
def three_d_ui(func="a**3", x_label="a", y_label="y"):
    return ui.page_fluid(
        ui.card(
            ui.card_header("3D Plot"),  # Title of the card

            # Layout that includes sidebar + main content area
            ui.layout_sidebar(
                ui.sidebar(
                    # Slider for selecting x-axis range in 3D plot
                    ui.input_slider("x_range_3d", f"Select range for {x_label}:", min=-100, max=100, value=[-10, 10]),
                    # Slider for selecting y-axis range in 3D plot
                    ui.input_slider("y_range_3d", f"Select range for {y_label}:", min=-100, max=100, value=[-10, 10]),
                    open="closed"  # Sidebar starts collapsed by default
                ),
                ui.output_ui("plot_3d"),  # Placeholder where the 3D plot will be rendered
                ui.input_action_button("reset_3d", "RESET")  # Button to reset sliders
            )
        )
    )

# ====================== 3D PLOT SERVER MODULE ======================
# This module handles the backend logic for rendering the 3D surface plot.
# It listens to slider inputs and regenerates the plot accordingly.
@module.server
def three_d_server(input, output, session, func="x**2", x_label="x", y_label="y"):

    # This reactive block resets the slider values when the reset button is clicked
    @reactive.effect
    def reset_sliders_and_plot():
        if input.reset_3d() > 0:
            # Reset x and y range sliders to default values [-10, 10]
            session.send_input_message("x_range_3d", {"value": [-10, 10]})
            session.send_input_message("y_range_3d", {"value": [-10, 10]})

    # Main output rendering for the 3D surface plot
    @output
    @render.ui
    def plot_3d():
        # Get the current slider-selected ranges for x and y axes
        x_range = input.x_range_3d() if input.x_range_3d is not None else [-10, 10]
        y_range = input.y_range_3d() if input.y_range_3d is not None else [-10, 10]

        try:
            # Create 50 evenly spaced values across the selected x and y ranges
            x = np.linspace(x_range[0], x_range[1], 50)
            y = np.linspace(y_range[0], y_range[1], 50)
            X, Y = np.meshgrid(x, y)  # Generate 2D grid coordinates for surface plotting

            # Evaluate the Z-axis values using the user-defined expression
            Z = eval(func, {x_label: X, y_label: Y, "np": np}) if func else np.zeros_like(X)

            # Create 3D surface plot using Plotly
            fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y)] if Z is not None else [])
            fig.update_layout(
                scene=dict(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    zaxis_title=f'f({x_label}, {y_label})',  # Dynamic label based on inputs
                ),
                title=f'3D Plot for {x_label} and {y_label}',  # Chart title
            )

            # Convert the plot to HTML and return it to display in Shiny app
            plot_html = pio.to_html(fig, full_html=True)
            return ui.HTML(plot_html)

        except Exception as e:
            # In case of error during plotting or evaluation, display the error in plot area
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[0], y=[0], mode='text',
                                     text=f"Error: {e}", textposition='middle center'))
            plot_html = pio.to_html(fig, full_html=True)
            return ui.HTML(plot_html)

# ====================== SCATTER PLOT UI MODULE ======================
# UI layout for displaying a scatter plot loaded from Excel file
@module.ui
def scatter_ui(file_name, x_label, y_label):
    return ui.page_fluid(
        ui.card(
            ui.card_header("Scatter Plot"),  # Title of the card

            # Sidebar layout with plot and reset button
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_action_button("reset_scatter", "RESET"),  # Button to reset or refresh plot
                    open="closed"  # Sidebar is collapsed initially
                ),
                ui.output_ui("plot_scatter")  # Placeholder where the scatter plot will render
            )
        )
    )

# ====================== SCATTER PLOT SERVER MODULE ======================
# Handles the server-side logic for generating a scatter plot from Excel data
@module.server
def scatter_server(input, output, session, file_name, x_label, y_label):

    # This reactive effect runs if you ever want to reset plot settings
    @reactive.effect
    def reset_plot():
        if input.reset_scatter() > 0:
            # Add reset logic here if needed (e.g., clearing filters, selections)
            pass

    # Output rendering function for the scatter plot
    @output
    @render.ui
    def plot_scatter():
        try:
            # Load the Excel file as a DataFrame
            df = pd.read_excel(file_name)

            # Check if specified columns exist in the DataFrame
            if x_label in df.columns and y_label in df.columns:
                x = df[x_label]
                y = df[y_label]

                # Create scatter plot using Plotly
                fig = go.Figure(data=[
                    go.Scatter(x=x, y=y, mode='markers', name='Scatter Plot')
                ])
                fig.update_layout(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    title=f'Scatter Plot for {x_label} vs {y_label}',
                )

                # Convert plot to HTML and return for UI rendering
                plot_html = pio.to_html(fig, full_html=True)
                return ui.HTML(plot_html)

            else:
                # Error: specified column not found in data
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[0], y=[0], mode='text',
                    text=f"Error: Columns '{x_label}' or '{y_label}' not found",
                    textposition='middle center'
                ))
                return ui.HTML(pio.to_html(fig, full_html=True))

        except Exception as e:
            # Catch-all for any unexpected error during plotting
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[0], y=[0], mode='text',
                text=f"Error: {e}", textposition='middle center'
            ))
            return ui.HTML(pio.to_html(fig, full_html=True))
