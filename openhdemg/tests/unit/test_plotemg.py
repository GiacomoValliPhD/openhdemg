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
    Figure_Layout_Manager, Figure_Subplots_Layout_Manager,
    plot_emgsig, plot_differentials, plot_refsig, plot_mupulses, plot_ipts,
    plot_idr, plot_smoothed_dr, plot_muaps, plot_muap, plot_muaps_for_cv,
)
from openhdemg.library.electrodes import sort_rawemg
from openhdemg.library.muap import diff, double_diff, sta, st_muap, xcc_sta
from openhdemg.library.tools import compute_svr, delete_mus
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


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

        # Test final_kwargs type
        self.assertIsInstance(final_kwargs, tuple)
        self.assertIsInstance(final_kwargs[0], dict)
        self.assertIsInstance(final_kwargs[1], dict)
        self.assertIsInstance(final_kwargs[2], dict)
        # Test that a figure was returned
        self.assertIsInstance(fig_manager.figure, plt.Figure)
        # Test that the figure has 2 axes
        self.assertTrue(len(fig_manager.figure.axes) == 2)
        # Test other plot properties
        self.assertEqual(ax1.get_ylabel(), "Channels (N°)")
        self.assertEqual(ax2.get_ylabel(), "MVC (%)")

        plt.close()

    def test_Figure_Subplots_Layout_Manager(self):
        """
        Test the Figure_Subplots_Layout_Manager class.
        """

        # Test with single line2d_kwargs_ax1
        fig, axes = plt.subplots(nrows=3, ncols=3)
        x = np.linspace(0, 4 * np.pi, 500)
        base_signal = np.sin(x)
        for row in axes:
            for ax in row:
                noisy_signal = base_signal + np.random.normal(
                    scale=0.4, size=base_signal.shape,
                )
                ax.plot(x, noisy_signal)
                ax.plot(x, base_signal)
                ax.set_xticks([])
                ax.set_yticks([])

        line2d_kwargs_ax1 = {
            "color": "tab:red",
            "alpha": 1,
            "linewidth": 0.2,
        }

        fig_manager = Figure_Subplots_Layout_Manager(figure=fig)
        fig_manager.set_line2d_from_kwargs(
            line2d_kwargs_ax1=line2d_kwargs_ax1,
        )
        fig_manager.set_layout(tight_layout=True, despine="2yaxes")

        # Test that a figure was returned
        self.assertIsInstance(fig_manager.figure, plt.Figure)
        # Test that the figure has 9 axes
        self.assertTrue(len(fig_manager.figure.axes) == 9)

        plt.close()

        # Test with multiple line2d_kwargs_ax1
        fig, axes = plt.subplots(nrows=3, ncols=3)
        x = np.linspace(0, 4 * np.pi, 500)
        base_signal = np.sin(x)
        for row in axes:
            for ax in row:
                noisy_signal = base_signal + np.random.normal(
                    scale=0.4, size=base_signal.shape,
                )
                ax.plot(x, noisy_signal)
                ax.plot(x, base_signal)
                ax.set_xticks([])
                ax.set_yticks([])

        line2d_kwargs_ax1 = [
            {
                "color": "tab:red",
                "alpha": 1,
                "linewidth": 0.2,
            },
            {
                "color": "tab:blue",
                "linewidth": 3,
                "alpha": 0.6,
            },
        ]

        fig_manager = Figure_Subplots_Layout_Manager(figure=fig)
        fig_manager.set_line2d_from_kwargs(
            line2d_kwargs_ax1=line2d_kwargs_ax1,
        )
        fig_manager.set_layout(tight_layout=False, despine="all")

        # Test that a figure was returned
        self.assertIsInstance(fig_manager.figure, plt.Figure)
        # Test that the figure has 9 axes
        self.assertTrue(len(fig_manager.figure.axes) == 9)

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

        # Test munumber with a single MU
        emgfile = emg_from_samplefile()
        emgfile = delete_mus(
            emgfile, munumber=[*range(1, emgfile["NUMBER_OF_MUS"])],
        )
        fig = plot_mupulses(
            emgfile, munumber="all", linelengths=0.9, addrefsig=False,
            timeinseconds=True, tight_layout=True,
            line2d_kwargs_ax1=self.line2d_kwargs_ax1,
            line2d_kwargs_ax2=self.line2d_kwargs_ax2,
            axes_kwargs=self.axes_kwargs,
            showimmediately=False,
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)

        plt.close()

        # Test munumber with a single empty MU
        emgfile = emg_from_samplefile()
        emgfile["MUPULSES"][0] = np.empty(0)
        emgfile = delete_mus(
            emgfile, munumber=[*range(1, emgfile["NUMBER_OF_MUS"])],
        )
        fig = plot_mupulses(
            emgfile, munumber="all", linelengths=0.9, addrefsig=False,
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

    def test_plot_muaps(self):
        """
        Test the plot_muaps function.
        """

        sorted_rawemg = sort_rawemg(
            emgfile=self.emgfile,
            code="GR08MM1305",
            orientation=180,
            dividebycolumn=True,
        )
        sorted_rawemg = diff(sorted_rawemg=sorted_rawemg)
        n_channels = sum(df.shape[1] for df in sorted_rawemg.values())
        sta_ = sta(
            emgfile=self.emgfile,
            sorted_rawemg=sorted_rawemg,
            firings="all",
            timewindow=50,
        )

        fig = plot_muaps(
            sta_dict=sta_[1],
            title="MUAPs from SD STA",
            line2d_kwargs_ax1=None,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

        # Test multiple MUAPS
        fig = plot_muaps(
            sta_dict=[sta_[1], sta_[2]],
            title="MUAPs from SD STA",
            line2d_kwargs_ax1=None,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

        # Test line2d_kwargs_ax1, single
        line2d_kwargs_ax1 = {
            "color": "tab:red",
            "alpha": 1,
            "linewidth": 0.2,
        }
        fig = plot_muaps(
            sta_dict=[sta_[1], sta_[2]],
            title="MUAPs from SD STA",
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

        # Test line2d_kwargs_ax1, single, and tight layout
        line2d_kwargs_ax1 = {
            "color": "tab:red",
            "alpha": 1,
            "linewidth": 0.2,
        }
        fig = plot_muaps(
            sta_dict=sta_[1],
            title="MUAPs from SD STA",
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            tight_layout=True,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

        # Test line2d_kwargs_ax1, multiple
        line2d_kwargs_ax1 = [
            {
                "color": "tab:red",
                "alpha": 1,
                "linewidth": 0.2,
            },
            {
                "color": "tab:blue",
                "linewidth": 3,
                "alpha": 0.6,
            },
        ]
        fig = plot_muaps(
            sta_dict=[sta_[1], sta_[2]],
            title="MUAPs from SD STA",
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

        # Test with an empty MU
        emgfile = emg_from_samplefile()
        emgfile["MUPULSES"][0] = np.empty(0)

        sorted_rawemg = sort_rawemg(
            emgfile=emgfile,
            code="GR08MM1305",
            orientation=180,
            dividebycolumn=True,
        )
        sorted_rawemg = diff(sorted_rawemg=sorted_rawemg)
        n_channels = sum(df.shape[1] for df in sorted_rawemg.values())
        sta_ = sta(
            emgfile=emgfile,
            sorted_rawemg=sorted_rawemg,
            firings="all",
            timewindow=50,
        )

        fig = plot_muaps(
            sta_dict=sta_[0],
            title="MUAPs from SD STA",
            line2d_kwargs_ax1=None,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

    def test_plot_muap(self):
        """
        Test the plot_muap function.
        """

        sorted_rawemg = sort_rawemg(
            emgfile=self.emgfile,
            code="GR08MM1305",
            orientation=180,
            dividebycolumn=True,
        )
        sorted_rawemg = diff(sorted_rawemg=sorted_rawemg)
        stmuap = st_muap(
            emgfile=self.emgfile,
            sorted_rawemg=sorted_rawemg,
            timewindow=30,
        )

        fig = plot_muap(
            emgfile=self.emgfile,
            stmuap=stmuap,
            munumber=2,
            column="col3",
            channel=8,
            channelprog=True,
            average=True,
            timeinseconds=True,
            figsize=[20, 15],
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)

        plt.close()

        # Test average
        fig = plot_muap(
            emgfile=self.emgfile,
            stmuap=stmuap,
            munumber=2,
            column="col3",
            channel=8,
            channelprog=True,
            average=False,
            timeinseconds=True,
            figsize=[20, 15],
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 1)

        plt.close()

        # Test channelprog
        fig = plot_muap(
            emgfile=self.emgfile,
            stmuap=stmuap,
            munumber=2,
            column="col3",
            channel=50,
            channelprog=False,
            average=True,
            timeinseconds=True,
            figsize=[20, 15],
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)

        plt.close()

        # Test timeinseconds
        fig = plot_muap(
            emgfile=self.emgfile,
            stmuap=stmuap,
            munumber=2,
            column="col3",
            channel=50,
            channelprog=False,
            average=True,
            timeinseconds=False,
            figsize=[20, 15],
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)

        plt.close()

        # Test kwargs
        for average in [True, False]:
            for line2d_kwargs_ax1 in [self.line2d_kwargs_ax1, None]:
                for line2d_kwargs_ax2 in [self.line2d_kwargs_ax2, None]:
                    fig = plot_muap(
                        emgfile=self.emgfile,
                        stmuap=stmuap,
                        munumber=2,
                        column="col3",
                        channel=50,
                        channelprog=False,
                        average=average,
                        timeinseconds=True,
                        figsize=[20, 15],
                        line2d_kwargs_ax1=line2d_kwargs_ax1,
                        line2d_kwargs_ax2=line2d_kwargs_ax2,
                        axes_kwargs=self.axes_kwargs,
                        showimmediately=False,
                    )

                    self.assertIsInstance(fig, plt.Figure)
                    self.assertTrue(
                        len(fig.axes) == 2 if average else 1
                    )

                    plt.close()

        # Test with an empty MU
        emgfile = emg_from_samplefile()
        emgfile["MUPULSES"][0] = np.empty(0)

        sorted_rawemg = sort_rawemg(
            emgfile=emgfile,
            code="GR08MM1305",
            orientation=180,
            dividebycolumn=True,
        )
        sorted_rawemg = diff(sorted_rawemg=sorted_rawemg)
        stmuap = st_muap(
            emgfile=emgfile,
            sorted_rawemg=sorted_rawemg,
            timewindow=30,
        )

        fig = plot_muap(
            emgfile=emgfile,
            stmuap=stmuap,
            munumber=0,
            column="col3",
            channel=8,
            channelprog=True,
            average=True,
            timeinseconds=True,
            figsize=[20, 15],
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == 2)

        plt.close()

    def test_plot_muaps_for_cv(self):
        """
        Test the plot_muaps_for_cv function.
        """

        sorted_rawemg = sort_rawemg(
            self.emgfile,
            code="GR08MM1305",
            orientation=180,
            dividebycolumn=True
        )
        dd = double_diff(sorted_rawemg)
        n_channels = sum(df.shape[1] for df in dd.values())
        sta_ = sta(
            emgfile=self.emgfile,
            sorted_rawemg=dd,
            firings="all",
            timewindow=50,
        )
        xcc_sta_ = xcc_sta(sta_)
        line2d_kwargs_ax1 = {
            "color": "k",
            "linewidth": 1,
        }

        fig = plot_muaps_for_cv(
            sta_dict=sta_[0],
            xcc_sta_dict=xcc_sta_[0],
            tight_layout=False,
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

        # Test tight_layout and line2d_kwargs_ax1
        line2d_kwargs_ax1 = {
            "color": "k",
            "linewidth": 1,
        }

        fig = plot_muaps_for_cv(
            sta_dict=sta_[0],
            xcc_sta_dict=xcc_sta_[0],
            tight_layout=True,
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()

        # Test with linear array
        array_sta = {"col0": sta_[0]["col1"]}
        array_xcc_sta = {"col0": xcc_sta_[0]["col1"]}

        fig = plot_muaps_for_cv(
            sta_dict=array_sta,
            xcc_sta_dict=array_xcc_sta,
            tight_layout=True,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == len(sta_[0]["col1"].columns))

        plt.close()

        # Test with an empty MU
        emgfile = emg_from_samplefile()
        emgfile["MUPULSES"][0] = np.empty(0)

        sorted_rawemg = sort_rawemg(
            emgfile,
            code="GR08MM1305",
            orientation=180,
            dividebycolumn=True
        )
        dd = double_diff(sorted_rawemg)
        n_channels = sum(df.shape[1] for df in dd.values())
        sta_ = sta(
            emgfile=emgfile,
            sorted_rawemg=dd,
            firings="all",
            timewindow=50,
        )
        xcc_sta_ = xcc_sta(sta_)
        line2d_kwargs_ax1 = {
            "color": "k",
            "linewidth": 1,
        }

        fig = plot_muaps_for_cv(
            sta_dict=sta_[0],
            xcc_sta_dict=xcc_sta_[0],
            tight_layout=False,
            line2d_kwargs_ax1=line2d_kwargs_ax1,
            showimmediately=False,
        )

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(len(fig.axes) == n_channels)

        plt.close()


if __name__ == '__main__':
    unittest.main()
