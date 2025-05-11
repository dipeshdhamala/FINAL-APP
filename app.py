from libfile import line_ui, line_server  # Import custom UI and server logic from external file
from shiny import ui, App  # Import core Shiny components for UI and application
import re  # Used for regular expression parsing
import os  # Used to work with file paths

# ====================== GLOBAL STORAGE ======================
line_plots = {}         # Dictionary to store plot configuration (functions, labels, etc.) for each unique ID
variable_store = {}     # Stores user-defined variables from the givefile (e.g., kf = ...)

# ====================== PARSE COMMANDS AND GENERATE COMPONENTS ======================
def create_ui_and_server(commands):
    ui_components = []       # List to hold all UI components that will be displayed on the app
    server_functions = []    # List to hold all server functions that will run backend logic

    for command in commands:
        # ----------- IGNORE COMMENTS AND EMPTY LINES -----------
        if command.startswith('#') or not command.strip():
            continue  # Skip this loop iteration if the command is a comment or blank

        # ----------- HANDLE VARIABLE ASSIGNMENTS -----------
        # Check if it's a variable assignment like: kf = expression
        if '=' in command and not command.strip().startswith("line("):
            match = re.match(r'\s*(\w+)\s*=\s*(.*)', command)  # Use regex to extract name and value
            if match:
                var_name = match.group(1).strip()      # Variable name (e.g., kf)
                var_expr = match.group(2).strip()      # Assigned expression (e.g., k * exp(...))
                variable_store[var_name] = var_expr    # Store in the global dictionary
                continue  # Skip further processing for this line

        # ----------- PARSE FUNCTION CALL: line(...) or sliderupdate(...) -----------
        parts = command.split('(', 1)  # Split at first '(' to isolate function name and arguments
        if len(parts) != 2:
            raise ValueError(f"Invalid command format: {command}")

        cmd_type = parts[0].strip()       # e.g., "line" or "sliderupdate"
        args_str = parts[1].rstrip(')')   # Get everything inside the parentheses

        try:
            # ----------- ADVANCED ARGUMENT PARSING -----------
            # This block safely splits arguments, even if lists contain commas
            args = []
            in_list = 0  # Tracks depth of nested brackets
            current_arg = ""
            for char in args_str:
                if char == '[':
                    in_list += 1
                elif char == ']':
                    in_list -= 1
                if char == ',' and in_list == 0:
                    args.append(current_arg.strip())  # Found a top-level argument separator
                    current_arg = ""
                else:
                    current_arg += char
            if current_arg:
                args.append(current_arg.strip())  # Add the final argument

            # ----------- CLEAN OR EVALUATE EACH ARGUMENT -----------
            for i, arg in enumerate(args):
                if arg.startswith('[') and arg.endswith(']'):
                    args[i] = eval(arg)  # Convert stringified list into a real Python list
                else:
                    args[i] = arg.strip().strip('"')  # Remove quotes and surrounding whitespace

        except Exception as e:
            raise ValueError(f"Invalid command format or arguments: {command}, error: {e}")

        # ====================== HANDLE LINE COMMAND ======================
        if cmd_type == 'line':
            if len(args) != 5:
                raise ValueError(f"Expected 5 arguments in line command, got {len(args)}: {command}")

            id = args[0]             # Unique ID for this plot block
            func_list1 = args[1]     # List of current-related expressions
            func_list2 = args[2]     # List of rate-related expressions
            x_label = args[3]        # X-axis label (e.g., voltage)
            y_label = args[4]        # Y-axis label (e.g., current or rate)

            # ----------- VARIABLE SUBSTITUTION FUNCTION -----------
            # Replaces all instances of defined variables (kf, kb, etc.) with their actual expressions
            def substitute_variables(func_list):
                updated_list = []
                for f in func_list:
                    if '=' in f:
                        before_eq, after_eq = f.split('=', 1)  # Separate LHS and RHS of equation
                        for var_name, var_expr in variable_store.items():
                            pattern = r'\b' + re.escape(var_name) + r'\b'  # Match full variable name
                            after_eq = re.sub(pattern, f'({var_expr})', after_eq)  # Replace safely
                        updated_list.append(before_eq.strip() + ' = ' + after_eq.strip())
                    else:
                        updated_list.append(f)  # If no '=', just append as-is
                return updated_list

            # Perform substitution on both function lists
            func_list1 = substitute_variables(func_list1)
            func_list2 = substitute_variables(func_list2)

            # Debug print to check how functions look after substitution
            print("func_list1:", func_list1)
            print("func_list2:", func_list2)

            # Store configuration in the global plot registry
            line_plots[id] = {
                'func_list1': func_list1,
                'func_list2': func_list2,
                'x_label': x_label,
                'y_label': y_label
            }

            # Generate corresponding UI and add to the UI components list
            ui_components.append(line_ui(id, func_list1, func_list2, x_label, y_label))

            # Create server logic for this plot and add it to server_functions
            server_functions.append(
                lambda id=id, func_list1=func_list1, func_list2=func_list2,
                       x_label=x_label, y_label=y_label:
                    line_server(id, func_list1, func_list2, x_label, y_label)
            )

        # ====================== HANDLE SLIDERUPDATE COMMAND ======================
        elif cmd_type == 'sliderupdate':
            id1 = args[0]                              # ID of the plot block to which this slider applies
            param = args[1]                            # Slider variable name
            min_val = float(args[2])                   # Minimum slider value
            max_val = float(args[3])                   # Maximum slider value
            value = args[4]                            # Default slider value (could be float or list)
            step = float(args[5])                      # Step size for slider movement
            label = args[6] if len(args) > 6 else None # Optional label override

            # Check if the ID exists and attach slider behavior
            if id1 in line_plots:
                plot = line_plots[id1]
                func_list1 = plot['func_list1']
                func_list2 = plot['func_list2']
                x_label = plot['x_label']
                y_label = plot['y_label']

                # Create a lambda function to dynamically update the slider on frontend
                server_functions.append(
                    lambda id=id1, func_list1=func_list1, func_list2=func_list2,
                           x_label=x_label, y_label=y_label,
                           param=param, min_val=min_val, max_val=max_val, value=value,
                           step=step, label=label:
                        line_server(id, func_list1, func_list2, x_label, y_label)["sliderupdate"](
                            param, min_val, max_val, value, step, label
                        )
                )

    # Return both lists for integration into the app (UI + server parts)
    return ui_components, server_functions


def read_commands_from_file(filename):
    with open(filename, 'r') as file:
        commands = [line.strip() for line in file if line.strip() and not line.startswith('#')]
    return commands

# Auto-locate givefile.py in same folder
current_dir = os.path.dirname(__file__)
filepath = os.path.join(current_dir, 'givefile.py')
print("Reading from:", filepath)

# Read and parse
commands = read_commands_from_file(filepath)
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
