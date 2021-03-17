"""
run as:
  python BMM_app.py
"""
from bluesky_widgets.utils.streaming import stream_documents_into_runs
from bluesky_widgets.qt import gui_qt
from bluesky_widgets.qt.figures import QtFigures
from bluesky_widgets.examples.utils.generate_msgpack_data import get_catalog
from bluesky_widgets.utils.list import EventedList 

from bluesky_widgets.qt.zmq_dispatcher import RemoteDispatcher
from bluesky_widgets.utils.streaming import stream_documents_into_runs

from bluesky_widgets.models.plot_builders import Lines


figures = EventedList()



models = []
import importlib

from bluesky_widgets.models.auto_plot_builders import AutoPlotter
from bluesky_widgets.models.plot_specs import Axes, Figure
class AutoBMMPlot(AutoPlotter):
    


    def handle_new_stream(self, run, stream_name):
        if stream_name != 'primary':
            return


        xx = run.metadata['start']['motors'][0]
        axes1 = Axes()
        axes2 = Axes()
        figure = Figure((axes1, axes2), title='It and I0')
        mapping = {'It' : [Lines(x=xx, ys=['It/I0',], max_runs=1),
                           Lines(x=xx, ys=['I0',],    max_runs=1)],
                   'I0' : [Lines(x=xx, ys=['I0',],    max_runs=1)],
                   #'Ir' : [Lines(x=xx, ys=['Ir/It','I0'], max_runs=1),],
                   'Ir' : [Lines(x=xx, ys=['It/I0',], max_runs=1, axes=axes1),
                           Lines(x=xx, ys=['I0',],    max_runs=1, axes=axes2)],
        }
        # if 'xs' in run.primary._descriptors[0]['hints']:
        #     rois = run.primary._descriptors[0]['hints']['xs']['fields']
        #     mapping['If'] = f'({" + ".join(rois)})/I0'
        #     run.events.completed.gconnect(lambda event : self.do_plot(run, mapping))
        # else:
        #     self.do_plot(run, mapping)

    #def do_plot(self, run, mapping):
        to_plot = run.metadata['start'].get('plot_request', 'It')
        #model = Lines(x=run.metadata['start']['motors'][0], ys=[mapping[to_plot],], max_runs=1,
        #              needs_streams=['primary',])
        for model in mapping[to_plot]:
            model.add_run(run)
            self.figures.append(model.figure) 
            self.plot_builders.append(model) 

address = 'localhost:5578'




model = AutoBMMPlot()

with gui_qt('BMM app'):
    dispatcher = RemoteDispatcher(address)
    dispatcher.subscribe(stream_documents_into_runs(model.add_run))
    view = QtFigures(model.figures)
    view.show()
    dispatcher.start()
