"""Gráficos diretos das variáveis disponíveis em qualquer caso do roteiro."""


def setplot(plotdata=None):
    if plotdata is None:
        from clawpack.visclaw.data import ClawPlotData
        plotdata = ClawPlotData()

    plotdata.clearfigures()
    figure = plotdata.new_plotfigure(name='Equação do telegrafista', figno=1)
    for row, (component, title) in enumerate(((0, 'u'), (1, 'u_t')), start=1):
        axes = figure.new_plotaxes()
        axes.axescmd = f'subplot(2,1,{row})'
        axes.title = title
        axes.xlimits = [-2, 2]
        axes.ylimits = 'auto'
        item = axes.new_plotitem(plot_type='1d_plot')
        item.plot_var = component
        item.plotstyle = '-'

    plotdata.printfigs = True
    plotdata.print_format = 'png'
    plotdata.print_framenos = 'all'
    plotdata.print_fignos = 'all'
    plotdata.html = True
    plotdata.latex = False
    return plotdata
