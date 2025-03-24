from testprogram import line_ui, line_server
from shiny import ui, App
import re

# Initialize line_plots dictionary
line_plots = {}
variable_store = {}  # Assuming a variable_store dictionary is defined somewhere

def create_ui_and_server(commands):
    ui_components = []
    server_functions = []


    for command in commands:
        # Ignore comments and empty lines
        if command.startswith('#') or not command.strip():
            continue

        if '=' in command:
            match = re.match(r'\s*(\w+)\s*=\s*(.*)', command)
            if match:
                var_name = match.group(1).strip()
                var_expr = match.group(2).strip()

                # Store the variable and its expression in the variable_store dictionary
                variable_store[var_name] = var_expr
                continue

        # Split command type and argument string
        parts = command.split('(', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid command format: {command}")

        cmd_type = parts[0].strip()
        args_str = parts[1].rstrip(')')

        # Manually handle arguments as strings
        try:
            # Split the arguments string by commas, respecting the structure inside lists
            args = []
            in_list = False
            current_arg = ""
            for char in args_str:
                if char == '[':
                    in_list = True
                elif char == ']':
                    in_list = False
                if char == ',' and not in_list:
                    args.append(current_arg.strip())
                    current_arg = ""
                else:
                    current_arg += char
            if current_arg:
                args.append(current_arg.strip())

            # Ensure that function list arguments are treated as lists, not evaluated as Python code
            for i, arg in enumerate(args):
                if arg.startswith('[') and arg.endswith(']'):
                    args[i] = eval(arg)  # Use eval safely for controlled cases (like list of equations)
                else:
                    args[i] = arg.strip().strip('"')

        except Exception as e:
            raise ValueError(f"Invalid command format or arguments: {command}, error: {e}")

        # Process line command
        if cmd_type == 'line':
            if len(args) != 4:
                raise ValueError(f"Invalid arguments for line command: {command}")

            id = args[0]
            func_list = args[1]  # Already a list due to the eval above
            x_label = args[2]
            y_label = args[3]
            for var_name, var_expr in variable_store.items():
                # Match the variable name as a whole word (e.g., 'k')
                pattern = r'\b' + re.escape(var_name) + r'\b'  # \b ensures it's a standalone 'k'

                updated_func_list = []
                for f in func_list:
                    # Split the string at the first '='
                    if '=' in f:
                        before_eq, after_eq = f.split('=', 1)
                        # Perform substitution only on the part after the '='
                        after_eq = re.sub(pattern, f'({var_expr})', after_eq)
                        # Combine the parts again
                        updated_func_list.append(before_eq + '=' + after_eq)
                    else:
                        updated_func_list.append(f)

                func_list = updated_func_list
                #print(func_list)


            line_plots[id] = {
                'func_list': func_list,
                'x_label': x_label,
                'y_label': y_label
            }
            # Create the UI and server components for the line plot
            ui_component = line_ui(id, func_list, x_label, y_label)
            ui_components.append(ui_component)

            server_functions.append(
                lambda id=id, func_list=func_list, x_label=x_label, y_label=y_label:
                    line_server(id, func_list, x_label=x_label, y_label=y_label)
            )

        # Process sliderupdate command
        elif cmd_type == 'sliderupdate':
            id1 = args[0]
            param = args[1]
            min_val = float(args[2])
            max_val = float(args[3])
            value = (args[4])  # Convert to float if necessary
            step = float(args[5])
            if len(args) > 6 and args[6] is not None:
                label = args[6]# Check if label exists
            else:
                label=None
                print (label)



            if id1 in line_plots:

                line_plot = line_plots[id1]
                func_list1 = line_plot['func_list']
                x_label1 = line_plot['x_label']
                y_label1 = line_plot['y_label']


                server_functions.append(
                    lambda id=id1, func_list=func_list1,x_label=x_label1,y_label=y_label1,param=param, min_val=min_val, max_val=max_val, value=value, step=step:
                        line_server(id, func_list, x_label, y_label)["sliderupdate"](param, min_val, max_val, value, step,label)
                )


    return ui_components, server_functions

def read_commands_from_file(filename):
    with open(filename, 'r') as file:
        commands = [line.strip() for line in file if line.strip() and not line.startswith('#')]
    return commands

# # Read commands from `givefile.py`
# commands = read_commands_from_file(r'E:\FINAL APP\givefile.py')

import os
# Dynamically find the correct file path
file_path = os.path.join(os.getcwd(), 'givefile.py')  # Assumes `givefile.py` is in the same directory

# Read commands from `givefile.py`
commands = read_commands_from_file(file_path)

# print(commands)  # Print the list of commands

# Create UI and server functions from commands
ui_components, server_functions = create_ui_and_server(commands)

# Sidebar definition with corrected MathJax script and syntax
sidebar = ui.sidebar(
    ui.h2("PLOT FUNCTION APP"),
    # Include MathJax script for LaTeX rendering
    ui.HTML("""
        <script type="text/javascript"
                src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
        </script>
    """),
    ui.markdown("""
        ### Butler-Volmer

        This is an interactive simulation for the Butler-Volmer (BV) equation under non-equilibrium and rate-controlled conditions, with an area ( A = 1 m<sup>2</sup>) and a number of electrons \( n = 1 \).

        You can change each variable (grouped under three dropdowns) using their respective editable sliders to observe how the BV current and reaction rate curves are affected.

        **Forward Reaction Rate**:
        $$ k_{f} = k_{0} \\exp\\left(-\\frac{\\beta F(V-U)}{RT}\\right) $$

        **Backward Reaction Rate**:
        $$ k_{b} = k_{0} \\exp\\left(\\frac{(1-\\beta) F(V-U)}{RT}\\right) $$

        **Net Current**:
        $$ i = i_{c} - i_{a} $$

        **Current Calculation**:
        $$ i = n F A k_{f} [\\text{Ox}] - n F A k_{b} [\\text{Red}] $$

        $$ i = n F A k_{0} \\left[ \\exp\\left(-\\frac{\\beta F (V - U)}{RT}\\right) - \\exp\\left( -\\frac{(1-\\beta) F (V - U)}{RT} \\right) \\right] $$
    """),
    width="40%",
    bg="#f8f8f8",
    open="open"
)

# Ensure MathJax triggers rendering after the sidebar is updated
app_ui = ui.page_fluid(
    ui.page_sidebar(
        sidebar,
        ui.page_fluid(*ui_components)  # Unpack the UI components into the main content area
    )
)

# Define the server function
def server(input, output, session):
    for func in server_functions:
        func()


# Create the Shiny app
app = App(app_ui, server)
