from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import warnings
from scipy.integrate import odeint
import sys
from dash import Dash, dcc, callback, Input, Output, html
from plotly import express as px

# Game defined as change in each population at each time step
def game(x, t, g1, g11, k, m):
    c1 = x[0]
    c11 = x[1]
    dxdt = [(g1 + k*c11) * c1,
            (g11 + m*c1) * c11]
    return dxdt

# Method to estimate the game over time. Error catching for when a solution can't be reached.
# If a solution can't be reached, reduce the time scale and try again.
def est_ode(game, init, max_time, g1, g11, k, m):
    t = np.arange(0, max_time, 1)
    success = False
    while(success==False):
        with warnings.catch_warnings(record=True):
            sol = odeint(game, init, t, args=(g1, g11, k, m), full_output=True)
            if sol[1]["message"] == "Integration successful.": 
                success = True
                sol = sol[0]
                sol[sol < 0] = 0
                return sol
            if len(t) > 10:
                t = t[:-2]
            else: return -sys.maxsize

def run(g1, g11, nude_k, nude_m, b6_k, b6_m, switch_time, end_time, c1_init, c11_init):
    # Run the game with nude parameters up to time to switch
    sol1 = est_ode(game, [c1_init, c11_init], switch_time+1, g1, g11, nude_k, nude_m)
    # Change k and m and continue the game
    sol2 = est_ode(game, [sol1[-1,0], sol1[-1,1]], end_time-switch_time, g1, g11, b6_k, b6_m)
    df = pd.DataFrame(columns=["Time", "C1", "C11"])
    df["Time"] = np.arange(0, end_time, 1)
    df["C1"] = np.concatenate([sol1[:,0], sol2[1:,0]])
    df["C11"] = np.concatenate([sol1[:,1], sol2[1:,1]])
    df = df.melt(id_vars="Time", value_vars=["C1", "C11"], var_name="Subline", value_name="Size")
    return df  

# Initial figure
df = run(0.135, 0.11, 0.15, -0.2, -0.5, -0.1, 10, 30, 0.1, 0.9)
fig = px.line(df, x="Time", y="Size", color="Subline")

app = Dash()

app.layout = [
    dcc.Graph(figure=fig, id="plot"),
    html.Div(html.Label("C1 Growth Rate")),
    dcc.Slider(min=0, max=0.2, step=0.01, value=0.135, id="g1_slider"),
    html.Div(html.Label("C11 Growth Rate")),
    dcc.Slider(min=0, max=0.2, step=0.01, value=0.11, id="g11_slider"),
    html.Div(html.Label("Nude k (C11 on C1)")),
    dcc.Slider(min=-1, max=1, step=0.1, value=0.15, id="nude_k_slider"),
    html.Div(html.Label("Nude m (C1 on C11)")),
    dcc.Slider(min=-1, max=1, step=0.1, value=-0.2, id="nude_m_slider"),
    html.Div(html.Label("B6 k (C11 on C1)")),
    dcc.Slider(min=-1, max=1, step=0.1, value=-0.5, id="b6_k_slider"),
    html.Div(html.Label("B6 m (C1 on C11)")),
    dcc.Slider(min=-1, max=1, step=0.1, value=-0.1, id="b6_m_slider"),
    html.Div(html.Label("Immunotherapy application time")),
    dcc.Slider(min=0, max=60, step=1, value=10, id="switch_time_slider"),
    html.Div(html.Label("End time")),
    dcc.Slider(min=0, max=60, step=1, value=30, id="end_time_slider"),
    html.Div(html.Label("C1 initial value")),
    dcc.Slider(min=0, max=1, step=0.1, value=0.1, id="c1_slider"),
    html.Div(html.Label("C11 initial value")),
    dcc.Slider(min=0, max=1, step=0.1, value=0.9, id="c11_slider")
]

@callback(
    Output(component_id="plot", component_property="figure"),
    Input(component_id="g1_slider", component_property="value"),
    Input(component_id="g11_slider", component_property="value"),
    Input(component_id="nude_k_slider", component_property="value"),
    Input(component_id="nude_m_slider", component_property="value"),
    Input(component_id="b6_k_slider", component_property="value"),
    Input(component_id="b6_m_slider", component_property="value"),
    Input(component_id="switch_time_slider", component_property="value"),
    Input(component_id="end_time_slider", component_property="value"),
    Input(component_id="c1_slider", component_property="value"),
    Input(component_id="c11_slider", component_property="value")
)
def update_graph(g1, g11, nude_k, nude_m, b6_k, b6_m, switch_time, end_time, c1, c11):
    df = run(g1, g11, nude_k, nude_m, b6_k, b6_m, switch_time, end_time, c1, c11)
    fig = px.line(df, x="Time", y="Size", color="Subline")
    return fig

if __name__ == "__main__":
    app.run(debug=True)