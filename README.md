# Interactive Simulation of the Butler-Volmer Equation

## Project Overview
This application is an interactive simulation designed to visualize the **Butler-Volmer (BV)** equation under non-equilibrium and rate-controlled conditions. It provides intuitive sliders for adjusting parameters and dynamic plots to explore the impact of changes in various variables. Note: you can view this app at https://dipeshapp.shinyapps.io/final_app/

## Features
- Interactive line plots for BV current and reaction rates.
- 3D visualization for complex relationships.
- Scatter plots for custom data visualization.
- Real-time slider adjustments for parameters.
- Intuitive sidebar 

## Requirements
The application uses Python and the Shiny library for building the interface, along with Bokeh for plotting. Install the dependencies using the following command:

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `shiny`
- `pandas`
- `numpy`
- `bokeh`
- `shinywidgets`
- `jupyter_bokeh`

## Usage

### Running the Application
1. Clone this repository and navigate to the project directory.
2. Ensure all dependencies are installed using the command:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application using:
   ```bash
   python app.py
   ```
4. Open the provided URL in your browser to access the interactive interface.

### Exploring the Interface
- **Sidebar**:
  - Adjustable sliders for parameters such as voltage, temperature, and reaction rate constants.
  - LaTeX-rendered equations for better understanding.
- **Dynamic Plots**:
  - Line plots for current and rate reactions.
  - 3D plots for multivariable interactions.
  - Scatter plots for visualizing data from uploaded files.

### Forward Reaction Rate (\(k_f\)):
\[ k_{f} = k \cdot \exp\left(-\frac{\beta F(V-U)}{RT}\right) \]

### Backward Reaction Rate (\(k_b\)):
\[ k_{b} = k \cdot \exp\left(\frac{(1-\beta) F(V-U)}{RT}\right) \]

### Net Current (\(i\)):
\[ i = n F A \left[ k_{f} [\text{Ox}] - k_{b} [\text{Red}] \right] \]


## Explanation of Main Code Components
### `app.py`
- **Purpose**: Serves as the entry point for the application. It reads commands, dynamically generates UI components, and initializes server functions.
- **Main Functionality**:
  - Reads commands from `givefile.py` to define the equations and slider configurations.
  - Dynamically creates UI components and server functions using the `create_ui_and_server` function.
  - Defines the main application layout, including a sidebar for parameter adjustments and plot rendering.

### `testprogram.py`
- **Purpose**: Provides modular components for UI and server logic.
- **Key Features**:
  - `line_ui`: Generates the UI for line plots, including sliders for parameters.
  - `line_server`: Handles the backend logic for updating line plots based on user inputs.
  - `extract_parameters`: A utility function to dynamically extract variables from equations for slider creation.

### `givefile.py`
- **Purpose**: Contains predefined equations and slider configurations.
- **Highlights**:
  - Defines key equations, such as the Butler-Volmer equation, for forward and backward reaction rates.
  - Configures sliders for parameters like `voltage`, `temperature (T)`, `reaction rate constant (k)`, and `transfer coefficient (beta)`.

### Dynamic Plotting
- **Line Plots**: Visualize relationships like current vs. voltage or rate constants.
- **3D Plots**: Explore multivariable interactions using sliders.
- **Scatter Plots**: Render custom data from Excel files for deeper analysis.

## Files
- **`app.py`**: Main application file integrating UI and server logic.
- **`testprogram.py`**: Contains reusable components for plotting and slider updates.
- **`givefile.py`**: Provides parameterized equations and slider settings.
- **`requirements.txt`**: Lists all Python dependencies.

## Contributions
Contributions to enhance this project are welcome. Feel free to open an issue or submit a pull request with suggestions or fixes.

## Author
Dipesh Dhamala
