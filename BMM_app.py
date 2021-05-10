"""
Run like:
python -m BMM-app.py
For each Run, it will generate thumbnails and save them to a temporary
directory. The filepaths will be printed to the stdout, one per line.
"""
import importlib
from functools import partial
import os
import tempfile
import msgpack
import msgpack_numpy as mpn
import time

from bluesky_widgets.utils.streaming import stream_documents_into_runs
from bluesky_widgets.qt import gui_qt
from bluesky_widgets.qt.figures import QtFigures
from bluesky_widgets.examples.utils.generate_msgpack_data import get_catalog
from bluesky_widgets.utils.list import EventedList 
from bluesky_widgets.qt.zmq_dispatcher import RemoteDispatcher
from bluesky_widgets.utils.streaming import stream_documents_into_runs
from bluesky_widgets.models.plot_builders import Lines
from bluesky_widgets.models.auto_plot_builders import AutoPlotter
from bluesky_widgets.models.plot_specs import Axes, Figure
from bluesky_kafka import RemoteDispatcher
from bluesky_widgets.headless.figures import HeadlessFigures
from bluesky_widgets.models.utils import run_is_live_and_not_completed

figures = EventedList()
models = []


class AutoBMMPlot(AutoPlotter):

    def handle_new_stream(self, run, stream_name):
        if stream_name != 'primary':
            return

        xx = run.metadata['start']['motors'][0]
        to_plot = run.metadata['start'].get('plot_request', 'It')
        models = []
        figures = []
        if to_plot == "It":
            axes1 = Axes()
            figure1 = Figure((axes1,), title="It/I0")
            figures.append(figure1)
            models.append(
                Lines(x=xx, ys=['It/I0',], max_runs=1, axes=axes1)
            )
            axes2 = Axes()
            figure2 = Figure((axes2,), title="I0")
            figures.append(figure2)
            models.append(
                Lines(x=xx, ys=['I0',],    max_runs=1, axes=axes2)
            )
        elif to_plot == "I0":
            axes = Axes()
            figure = Figure((axes,), title="I0")
            figures.append(figure)
            models.append(
                Lines(x=xx, ys=['I0',],    max_runs=1, axes=axes)
            )
        elif to_plot == "Ir":
            axes1 = Axes()
            axes2 = Axes()
            figure = Figure((axes1, axes2), title='It and I0')
            figures.append(figure)
            models.append(
                Lines(x=xx, ys=['It/I0',], max_runs=1, axes=axes1)
            )
            models.append(
                Lines(x=xx, ys=['I0',],    max_runs=1, axes=axes2)
            )
        else:
            # Plot nothing.
            pass
        for model in models:
            model.add_run(run)
            self.plot_builders.append(model) 
        self.figures.extend(figures) 


def export_thumbnails_when_complete(run):
    "Given a BlueskyRun, export thumbnail(s) to a directory when it completes."
    model = AutoBMMPlot()
    model.add_run(run)
    view = HeadlessFigures(model.figures)

    uid = run.metadata["start"]["uid"]
    directory = os.path.join(tempfile.gettempdir(), "bluesky_widgets_example", uid)
    os.makedirs(directory, exist_ok=True)

    # If the Run is already done by the time we got it, export now.
    # Otherwise, schedule it to export whenever it finishes.
    def export(*args, **kwargs):
        filenames = view.export_all(directory)
        print("\n".join(f'"{filename}"' for filename in filenames))
        view.close()


    if run_is_live_and_not_completed(run):
        run.events.new_data.connect(export)
    else:
        export()


if __name__ == "__main__":
    bootstrap_servers = "kafka1.nsls2.bnl.gov:9092,kafka2.nsls2.bnl.gov:9092,kafka3.nsls2.bnl.gov:9092"
    kafka_deserializer = partial(msgpack.loads, object_hook=mpn.decode)
    topics = ["bmm.bluesky.runengine.documents"]
    consumer_config = {"auto.commit.interval.ms": 100, "auto.offset.reset": "latest"}

    dispatcher = RemoteDispatcher(
        topics=topics,
        bootstrap_servers=bootstrap_servers,
        group_id="widgets_test",
        consumer_config=consumer_config,
    )

    dispatcher.subscribe(stream_documents_into_runs(export_thumbnails_when_complete))
    dispatcher.subscribe(lambda name, doc: print(name, doc.get('uid'), doc.get('descriptor')))
    dispatcher.start()
