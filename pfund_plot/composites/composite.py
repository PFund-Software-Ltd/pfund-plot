# TEMP
# composites are plots combined together on the same canvas
# it can be used to perform comparison analysis, create a graph that has the price line, equity curve etc. 

# use plotly for composite plots
class CompositePlot:
    def __init__(self, plots):
        self.plots = plots

    def render(self):
        # Implement logic to combine plots
        # This is non-trivial and may require standardizing on a single backend
        pass