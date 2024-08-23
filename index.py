import warnings
from scipy.integrate import odeint
import sys
from dash import Dash, dcc, callback, Input, Output, html
from plotly import express as px

class MainApplication:
    def __init__(self):
        self.__app = Dash(

        )

        self.set_layout()

    @property
    def app(self):
        return self.__app

    def set_layout(self):
        # Initial figure
        sol_c1, sol_c11 = self.run(0.135, 0.11, 0.15, -0.2, -0.5, -0.1, 10, 30, 0.1, 0.9)
        t = list(range(0, 30, 1))
        fig = px.line(x=t, y=[sol_c1, sol_c11])  

        self.app.layout = [
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
            sol_c1, sol_c11 = self.run(g1, g11, nude_k, nude_m, b6_k, b6_m, switch_time, end_time, c1, c11)
            t = list(range(0, end_time, 1))
            fig = px.line(x=t, y=[sol_c1, sol_c11])
            return fig


    # Game defined as change in each population at each time step
    def game(self, x, t, g1, g11, k, m):
        c1 = x[0]
        c11 = x[1]
        dxdt = [(g1 + k*c11) * c1,
                (g11 + m*c1) * c11]
        return dxdt

    # Method to estimate the game over time. Error catching for when a solution can't be reached.
    # If a solution can't be reached, reduce the time scale and try again.
    def est_ode(self, game, init, max_time, g1, g11, k, m):
        t = list(range(0, max_time, 1))
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

    def run(self, g1, g11, nude_k, nude_m, b6_k, b6_m, switch_time, end_time, c1_init, c11_init):
        # Run the game with nude parameters up to time to switch
        sol1 = self.est_ode(self.game, [c1_init, c11_init], switch_time+1, g1, g11, nude_k, nude_m)
        # Change k and m and continue the game
        sol2 = self.est_ode(self.game, [sol1[-1,0], sol1[-1,1]], end_time-switch_time, g1, g11, b6_k, b6_m)
        return sol1[:,0].tolist() + sol2[1:,0].tolist(), sol1[:,1].tolist() + sol2[1:,1].tolist()

Application = MainApplication()
app = Application.app
server = Application.app.server

if __name__ == "__main__":
    Application.app.run(port=6969, dev_tools_ui=True, debug=True, host="127.0.0.1")
    # Application.app.run()