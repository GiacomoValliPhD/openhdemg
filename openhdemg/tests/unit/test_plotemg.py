"""
To run the tests using unittest, execute from the openhdemg/tests directory:
    python -m unittest discover

First, you should dowload all the files necessary for the testing and store
them inside openhdemg/tests/fixtures. The files are available at:
https://drive.google.com/drive/folders/1suCZSils8rSCs2E3_K25vRCbN3AFDI7F?usp=sharing

IMPORTANT: Do not alter the content of the dowloaded folder!

WARNING!!! Since the library's functions perform complex tasks and return
complex data structures, these tests can verify that no critical errors occur,
but the accuracy of each function must be assessed independently upon creation,
or at each revision of the code.

WARNING!!! - UNTESTED FUNCTIONS: none
"""

import unittest
from openhdemg.library.openfiles import emg_from_samplefile
from openhdemg.library.plotemg import (
    Figure_Layout_Manager, plot_emgsig, plot_differentials, plot_refsig,
    plot_mupulses, plot_ipts, plot_idr, plot_smoothed_dr,
)
from openhdemg.library.electrodes import sort_rawemg
from openhdemg.library.muap import double_diff
from openhdemg.library.tools import compute_svr
import matplotlib.pyplot as plt
import pandas as pd


class TestPlotEMG(unittest.TestCase):
    """
    Test the functions/classes in the plotemg module.
    """

    def setUp(self):
        """
        Initialize variables for each test.

        This method is called before each test function runs.
        """

        # Load the decomposed samplefile
        self.emgfile = emg_from_samplefile()

        self.line2d_kwargs_ax1 = {
            "linewidth": 0.5,
            "alpha": 1,
        }

        self.line2d_kwargs_ax2 = {
            "linewidth": 2,
            "color": '0.4',
            "alpha": 1,
        }

        self.axes_kwargs = {
            "grid": {
                "visible": True,
                "axis": "both",
                "color": "gray",
                "linestyle": "--",
                "linewidth": 0.5,
                "alpha": 0.7
            },
            "labels": {
                "xlabel": None,
                "ylabel_sx": "Channels (N°)",
                "ylabel_dx": "MVC (%)",
                "title": "Custom figure title",
                "xlabel_size": 12,
                "xlabel_color": "black",
                "ylabel_sx_size": 12,
                "ylabel_sx_color": "black",
                "ylabel_dx_size": 12,
                "ylabel_dx_color": "black",
                "labelpad": 6,
                "title_size": 12,
                "title_color": "black",
                "title_pad": 14,
            },
            "ticks_ax1": {
                "axis": "both",
                "labelsize": 10,
                "labelrotation": 0,
                "direction": "out",
                "colors": "black",
            },
            "ticks_ax2": {
                "axis": "y",
                "labelsize": 10,
                "labelrotation": 0,
                "direction": "out",
                "colors": "black",
            }
        }

    def test_Figure_Layout_Manager(self):
        """
        Test the Figure_Layout_Manager class.
        """

        fig, ax1 = plt.subplots()
        ax1.plot([1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1])
        ax2 = ax1.twinx()
        ax2.plot([6, 5, 4, 3, 2, 1, 2, 3, 4, 5, 6])

        line2d_kwargs_ax1 = {
            "linewidth": 3,
            "alpha": 0.2,
        }
        line2d_kwargs_ax2 = {
            "linewidth": 1,
            "alpha": 0.2,
            "color": "red",
        }
        axes_kwargs = {
            "grid": {
                "visible": True,
                "axis": "both",
                "color": "gray",
            },
            "labels": {
                "xlabel": None,
                "ylabel_sx": "Channels (N°)",
                "ylabel_dx": "MVC (%)",
            },
        }

        fig_manager = Figure_Layout_Manager(figure=fig)
        final_kwargs = fig_manager.get_final_kwargs(
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            line2d_kwargs_ax2=line2d_kwargs_ax2,
            axes_kwargs=axes_kwargs,
        )
        fig_manager.set_style_from_kwargs()
        fig_manager.set_layout(tight_layout=True, despine="2yaxes")

        # Test that a figure was returned
        self.assertIsInstance(fig_manager.figure, plt.Figure)
        # Test that the figure has 2 axes
        self.assertTrue(len(fig_manager.figure.axes) == 2)
        # Test other plot properties
        self.assertEqual(ax1.get_ylabel(), "Channels (N°)")
        self.assertEqual(ax2.get_ylabel(), "MVC (%)")

        plt.close()

    def test_plot_emgsig(self):
        """
        Test the plot_emgsig function.
        """

        fig = plot_emgsig(
            self.emgfile, channels=[*range(0, 6)],
            manual_offset=0,
            addrefsig=False, timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test manual_offset
        fig = plot_emgsig(
            self.emgfile, channels=[*range(0, 6)],
            manual_offset=1000,
            addrefsig=False, timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test addrefsig
        fig = plot_emgsig(
            self.emgfile, channels=[*range(0, 6)],
            manual_offset=0,
            addrefsig=True, timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")
        self.assertEqual(fig.axes[1].get_ylabel(), "MVC (%)")

        plt.close()

        # Test timeinseconds
        fig = plot_emgsig(
            self.emgfile, channels=[*range(0, 6)],
            manual_offset=0,
            addrefsig=True, timeinseconds=False, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Samples")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")
        self.assertEqual(fig.axes[1].get_ylabel(), "MVC (%)")

        plt.close()

    def test_plot_differentials(self):
        """
        Test the plot_differentials function.
        """

        sorted_rawemg = sort_rawemg(
            emgfile=self.emgfile,
            code="GR08MM1305",
            orientation=180,
        )

        sd = double_diff(sorted_rawemg=sorted_rawemg)

        fig = plot_differentials(
            self.emgfile, differential=sd, column="col1",
            manual_offset=0,
            addrefsig=False, timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test manual_offset
        fig = plot_differentials(
            self.emgfile, differential=sd, column="col1",
            manual_offset=1000,
            addrefsig=False, timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test addrefsig
        fig = plot_differentials(
            self.emgfile, differential=sd, column="col1",
            manual_offset=0,
            addrefsig=True, timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")
        self.assertEqual(fig.axes[1].get_ylabel(), "MVC (%)")

        plt.close()

        # Test timeinseconds
        fig = plot_differentials(
            self.emgfile, differential=sd, column="col1",
            manual_offset=0,
            addrefsig=True, timeinseconds=False, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Samples")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")
        self.assertEqual(fig.axes[1].get_ylabel(), "MVC (%)")

        plt.close()

    def test_plot_refsig(self):
        """
        Test the plot_refsig function.
        """

        fig = plot_refsig(
            self.emgfile,
            timeinseconds=False, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Samples")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test timeinseconds
        fig = plot_refsig(
            self.emgfile,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

    def test_plot_mupulses(self):
        """
        Test the plot_mupulses function.
        """

        fig = plot_mupulses(
            self.emgfile, munumber="all", linelengths=0.9, addrefsig=True,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test timeinseconds
        fig = plot_mupulses(
            self.emgfile, munumber="all", linelengths=0.9, addrefsig=True,
            timeinseconds=False, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Samples")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test addrefsig
        fig = plot_mupulses(
            self.emgfile, munumber="all", linelengths=0.9, addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)

        plt.close()

        # Test munumber
        fig = plot_mupulses(
            self.emgfile, munumber=[1, 3, 4], linelengths=0.9, addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)

        plt.close()

        fig = plot_mupulses(
            self.emgfile, munumber=2, linelengths=0.9, addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)

        plt.close()

    def test_plot_ipts(self):
        """
        Test the plot_ipts function.
        """

        fig = plot_ipts(
            self.emgfile, munumber="all", addrefsig=True,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test addrefsig
        fig = plot_ipts(
            self.emgfile, munumber="all", addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test munumber
        fig = plot_ipts(
            self.emgfile, munumber=1, addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test munumber
        fig = plot_ipts(
            self.emgfile, munumber=[1, 3, 4], addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

    def test_plot_idr(self):
        """
        Test the plot_idr function.
        """

        line2d_kwargs_ax1 = {
            "marker": "d",
            "markersize": 7,
            "markerfacecolor": "k",
        }

        fig = plot_idr(
            self.emgfile, munumber="all", addrefsig=True,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test addrefsig
        fig = plot_idr(
            self.emgfile, munumber="all", addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test munumber
        fig = plot_idr(
            self.emgfile, munumber=1, addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test munumber
        fig = plot_idr(
            self.emgfile, munumber=[1, 3, 4], addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

    def test_plot_smoothed_dr(self):
        """
        Test the plot_smoothed_dr function.
        """

        svrfits = compute_svr(self.emgfile)
        smoothfits = pd.DataFrame(svrfits["gensvr"]).transpose()

        fig = plot_smoothed_dr(
            self.emgfile,
            smoothfits=smoothfits,
            munumber=0,
            addidr=False,
            stack=True,
            addrefsig=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test addidr and munumber
        fig = plot_smoothed_dr(
            self.emgfile,
            smoothfits=smoothfits,
            munumber=[0],
            addidr=True,
            stack=True,
            addrefsig=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test stack and munumber
        fig = plot_smoothed_dr(
            self.emgfile,
            smoothfits=smoothfits,
            munumber="all",
            addidr=True,
            stack=False,
            addrefsig=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        fig = plot_smoothed_dr(
            self.emgfile,
            smoothfits=smoothfits,
            munumber="all",
            addidr=True,
            stack=True,
            addrefsig=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        fig = plot_smoothed_dr(
            self.emgfile,
            smoothfits=smoothfits,
            munumber="all",
            addidr=False,
            stack=False,
            addrefsig=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        fig = plot_smoothed_dr(
            self.emgfile,
            smoothfits=smoothfits,
            munumber="all",
            addidr=False,
            stack=True,
            addrefsig=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()

        # Test addrefsig
        fig = plot_smoothed_dr(
            self.emgfile,
            smoothfits=smoothfits,
            munumber="all",
            addidr=True,
            stack=False,
            addrefsig=False,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)
        self.assertEqual(fig.axes[0].get_xlabel(), "Time (Sec)")
        self.assertEqual(fig.axes[0].get_ylabel(), "Channels (N°)")

        plt.close()


if __name__ == '__main__':
    unittest.main()
