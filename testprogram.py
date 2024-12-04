import re
from shiny import ui, module, reactive, render, App
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from shinywidgets import output_widget, bokeh_dependency, render_bokeh
from bokeh.palettes import Category10  # Bokeh color palette
slider_values = {}

# Function to extract variables after "=" excluding 'x'
def extract_parameters(expression, defined_vars, x_label):
    param_pattern = re.compile(r'([a-zA-Z]\w*)')
    matches = param_pattern.findall(expression)
    excluded = ['np', 'sin', 'cos', 'tan', 'log', 'exp', 'sqrt']
    return sorted([match for match in matches if match != x_label and match not in excluded and match not in defined_vars])

@module.ui
def line_ui(func_list, x_label, y_label):
    params = set()
    defined_vars = set([x_label])
    for func in func_list:
        _, expression = func.split('=')
        params.update(extract_parameters(expression, defined_vars, x_label))
        lhs_var = func.split('=')[0].strip()
        defined_vars.add(lhs_var)

    sliders = [
        ui.input_slider(f"{param}", f"Select value for {param}:", min=-10, max=10, value=1)
        for param in params
    ]

    return ui.page_fluid(
        ui.div(
            ui.card(
                ui.card_header("BV current Plot"),
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_slider("x_range_line", f"Select range for {x_label}:", min=-100, max=100, value=[-10, 10]),
                        *sliders,
                        ui.input_action_button("reset_line", "RESET", class_="btn-primary"),
                        width="40%",
                        open="closed"  # Reset button
                    ),
                    bokeh_dependency(),
                    output_widget("plot_line")
                ),
                height="600px",  # Set the height of the card
                fill=False  # Prevent the card from expanding to fill the container
            ),
            style="width: 600px;"  # Set the width of the card
        )
    )


@module.server
def line_server(input, output, session, func_list, x_label="x", y_label="y"):
    
    

    # Function to update slider values
    def sliderupdate(slider_name, min_val, max_val, default_val, step=None, label=None):
        slider_values[slider_name] = default_val

        if label is None:
            label = slider_name

        if step is None:
            step = abs((max_val + min_val) / 100)

        session.send_input_message(slider_name, {
            "label": label,
            "min": min_val,
            "max": max_val,
            "value": default_val,
            "step": step
        })


    @reactive.effect
    @reactive.event(input.reset_line)
    def _():

        original_value={}
        
        params = set()
        defined_vars = set([x_label])
        for func in func_list:
            _, expression = func.split('=')
            params.update(extract_parameters(expression, defined_vars, x_label))
            lhs_var = func.split('=')[0].strip()
            defined_vars.add(lhs_var)

        for param in params:
            # Check if the parameter is in slider_values
            if param in slider_values:
                # If it exists, reset to its stored value
                original_value[param] = slider_values[param]
                ui.update_slider(param, value=original_value[param])
            else:
                # If it does not exist, provide the default value
                ui.update_slider(param, value=1)  # Default value for parameters

        # Reset the x_range_line slider to its default value
        if "x_range_line" in slider_values:
            original_x_range = slider_values["x_range_line"]
            ui.update_slider("x_range_line", value=original_x_range)
        else:
            ui.update_slider("x_range_line", value=[-10, 10])  # Default value for x_range_line
        
    @render_bokeh
    def plot_line():
        x_range = input.x_range_line() if input.x_range_line is not None else [-10, 10]
        funcs = func_list[:]

        params = set()
        defined_vars = set([x_label])
        for func in funcs:
            _, expression = func.split('=')  # Split at '=' to get RHS
            params.update(extract_parameters(expression, defined_vars, x_label))
            defined_vars.add(func.split('=')[0].strip())

        param_values = {param: input[f"{param}"]() for param in params}

        try:
            x = np.linspace(x_range[0], x_range[1], 50)
            context = {x_label: x, "np": np}
            context.update(param_values)

            fig = figure(title=f'Line Plot for {x_label}', x_axis_label=x_label, y_axis_label=y_label,width=100,height=100)

            # Assign colors from Bokeh Category10 palette
            colors = Category10[10]

            # Iterate over functions and evaluate them with different colors
            for i, item in enumerate(funcs):
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

    return {
        "sliderupdate": sliderupdate
    }
# Define the UI for the 3D plot
@module.ui
def three_d_ui(func="a**3", x_label="a", y_label="y"):
    return ui.page_fluid(
        ui.card(
            ui.card_header("3D Plot"),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_slider("x_range_3d", "Select range for {x_label}:", min=-100, max=100, value=[-10, 10]),
                    ui.input_slider("y_range_3d", "Select range for {y_label}:", min=-100, max=100, value=[-10, 10]),
                    open="closed"  # Sidebar is initially closed
                ),
                ui.output_ui("plot_3d"),
                ui.input_action_button("reset_3d", "RESET")
            )
        )
    )

# Define the server function for the 3D plot
@module.server
def three_d_server(input, output, session, func="x**2", x_label="x", y_label="y"):
    @reactive.effect
    def reset_sliders_and_plot():
        if input.reset_3d() > 0:
            session.send_input_message("x_range_3d", {"value": [-10, 10]})
            session.send_input_message("y_range_3d", {"value": [-10, 10]})

    @output
    @render.ui
    def plot_3d():
        x_range = input.x_range_3d() if input.x_range_3d is not None else [-10, 10]
        y_range = input.y_range_3d() if input.y_range_3d is not None else [-10, 10]

        try:
            x = np.linspace(x_range[0], x_range[1], 50)
            y = np.linspace(y_range[0], y_range[1], 50)
            X, Y = np.meshgrid(x, y)

            # Using eval to evaluate the function
            Z = eval(func, {x_label: X, y_label: Y, "np": np}) if func else np.zeros_like(X)

            fig = go.Figure(data=[go.Surface(z=Z, x=X, y=Y)] if Z is not None else [])
            fig.update_layout(
                scene=dict(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    zaxis_title=f'f({x_label}, {y_label})',
                ),
                title=f'3D Plot for {x_label} and {y_label}',
            )

            plot_html = pio.to_html(fig, full_html=True)
            return ui.HTML(plot_html)
        except Exception as e:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[0], y=[0], mode='text', text=f"Error: {e}", textposition='middle center'))

            plot_html = pio.to_html(fig, full_html=True)
            return ui.HTML(plot_html)

# Define the UI for the scatter plot
@module.ui
def scatter_ui(file_name, x_label, y_label):
    return ui.page_fluid(
        ui.card(
            ui.card_header("Scatter Plot"),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_action_button("reset_scatter", "RESET"),
                    open="closed"  # Sidebar is initially closed
                ),
                ui.output_ui("plot_scatter")
            )
        )
    )

# Define the server function for the scatter plot
@module.server
def scatter_server(input, output, session, file_name, x_label, y_label):
    @reactive.effect
    def reset_plot():
        if input.reset_scatter() > 0:
            # Add reset logic if necessary, like clearing selections
            pass

    @output
    @render.ui
    def plot_scatter():
        try:
            # Load the data from the Excel file
            df = pd.read_excel(file_name)

            # Check if the specified columns exist in the dataframe
            if x_label in df.columns and y_label in df.columns:
                x = df[x_label]
                y = df[y_label]

                # Create the scatter plot
                fig = go.Figure(data=[go.Scatter(x=x, y=y, mode='markers', name='Scatter Plot')])
                fig.update_layout(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    title=f'Scatter Plot for {x_label} vs {y_label}',
                )

                # Convert the plot to HTML for rendering in the UI
                plot_html = pio.to_html(fig, full_html=True)
                return ui.HTML(plot_html)
            else:
                # Handle case where columns are not found
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=[0], y=[0], mode='text', text=f"Error: Columns '{x_label}' or '{y_label}' not found", textposition='middle center'))
                plot_html = pio.to_html(fig, full_html=True)
                return ui.HTML(plot_html)
        except Exception as e:
            # Handle errors and display them in the UI
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[0], y=[0], mode='text', text=f"Error: {e}", textposition='middle center'))
            plot_html = pio.to_html(fig, full_html=True)
            return ui.HTML(plot_html)


#get sliders 
@module.ui
def slider(label):
    return ui.input_slider("unique", label, 0, 100, 20)

@module.server
def sliderserver(input, output, session):
    @reactive.Calc
    def slidervalue():
        return input.unique
    return slidervalue()

