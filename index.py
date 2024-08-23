import warnings
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
        sol_t, sol_c1, sol_c11 = self.run(0.135, 0.11, 0.15, -0.2, -0.5, -0.1, 10, 30, 0.1, 0.9)
        # print(sol_t)
        # print(sol_c1)
        # print(sol_c11)
        fig = px.line(x=sol_t, y=[sol_c1, sol_c11])  
        fig.data[0].name = "C1"
        fig.data[1].name = "C11"

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
            sol_t, sol_c1, sol_c11 = self.run(g1, g11, nude_k, nude_m, b6_k, b6_m, switch_time, end_time, c1, c11)
            fig = px.line(x=sol_t, y=[sol_c1, sol_c11])#, labels={"wide_variable_0": "C1", "wide_variable_1": "C11"})
            fig.data[0].name = "C1"
            fig.data[0].legendgroup = "C1"
            fig.data[0].hovertemplate = fig.data[0].hovertemplate.replace("wide_variable_0", "C1")
            fig.data[1].name = "C11"
            fig.data[1].legendgroup = "C11"
            fig.data[1].hovertemplate = fig.data[0].hovertemplate.replace("wide_variable_1", "C11")
            fig.update_layout(legend_title = "Subline")
            return fig

    # Game defined as change in each population at each time step
    # (Yes, some parameters are worthless, leaving for now for consistency)
    def game_c1(self, t, c1, c11, g1, g11, k, m):
        return (g1 + k*c11) * c1
    def game_c11(self, t, c1, c11, g1, g11, k, m):
        return (g11 + m*c1) * c11
    
    def RungeKutta(self, x, y, z, dx, dydx, dzdx, g1, g11, k, m):
        # From https://primer-computational-mathematics.github.io/book/c_mathematics/numerical_methods/5_Runge_Kutta_method.html
        # x = time, y = c1, z = c11
        k1 = dx*dydx(x, y, z, g1, g11, k, m)
        h1 = dx*dzdx(x, y, z, g1, g11, k, m)
        k2 = dx*dydx(x+dx/2., y+k1/2., z+h1/2., g1, g11, k, m)
        h2 = dx*dzdx(x+dx/2., y+k1/2., z+h1/2., g1, g11, k, m)
        k3 = dx*dydx(x+dx/2., y+k2/2., z+h2/2., g1, g11, k, m)
        h3 = dx*dzdx(x+dx/2., y+k2/2., z+h2/2., g1, g11, k, m)
        k4 = dx*dydx(x+dx, y+k3, z+h3, g1, g11, k, m)
        h4 = dx*dzdx(x+dx, y+k3, z+h3, g1, g11, k, m)

        y = y + 1./6.*(k1+2*k2+2*k3+k4)
        z = z + 1./6.*(h1+2*h2+2*h3+h4)
        x = x + dx
        
        return x, y, z

    # Method to estimate the game over time. Error catching for when a solution can't be reached.
    # If a solution can't be reached, reduce the time scale and try again.
    def est_ode(self, c1, c11, max_time, g1, g11, k, m):
        # From https://primer-computational-mathematics.github.io/book/c_mathematics/numerical_methods/5_Runge_Kutta_method.html
        t = 0
        t_list = [t]
        c1_list = [c1]
        c11_list = [c11]
        while t < max_time:
            t, c1, c11 = self.RungeKutta(t, c1, c11, .1, self.game_c1, self.game_c11, g1, g11, k, m)
            t_list.append(t)
            c1_list.append(c1)
            c11_list.append(c11)
        return t_list, c1_list, c11_list

    def run(self, g1, g11, nude_k, nude_m, b6_k, b6_m, switch_time, end_time, c1_init, c11_init):
        # Run the game with nude parameters up to time to switch
        sol1_t, sol1_c1, sol1_c11 = self.est_ode(c1_init, c11_init, switch_time, g1, g11, nude_k, nude_m)
        # Change k and m and continue the game
        sol2_t, sol2_c1, sol2_c11 = self.est_ode(sol1_c1[-1], sol1_c11[-1], end_time-switch_time, g1, g11, b6_k, b6_m)
        sol2_t = [sol1_t[-1] + i for i in sol2_t]
        return sol1_t + sol2_t, sol1_c1 + sol2_c1, sol1_c11 + sol2_c11

Application = MainApplication()
app = Application.app
server = Application.app.server

if __name__ == "__main__":
    Application.app.run(port=6969, dev_tools_ui=True, debug=True, host="127.0.0.1")
    # Application.app.run()