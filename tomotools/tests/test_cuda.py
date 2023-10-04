import tomotools.datasets as ds
import matplotlib
import tomotools
import numpy
from tomotools import recon
import astra
import pytest


@pytest.mark.skipif(not astra.use_cuda(), reason="CUDA not detected")
class TestAlignCUDA:
    def test_test_align_cuda(self):
        stack = ds.get_needle_data(True)
        stack.test_align(thickness=200, cuda=True)
        fig = matplotlib.pylab.gcf()
        assert len(fig.axes) == 3


@pytest.mark.skipif(not astra.use_cuda(), reason="CUDA not detected")
class TestReconCUDA:
    def test_recon_fbp_gpu(self):
        stack = ds.get_needle_data(True)
        slices = stack.isig[:, 120:121].deepcopy()
        rec = slices.reconstruct('FBP', cuda=True)
        assert type(stack) is tomotools.base.TomoStack
        assert type(rec) is tomotools.base.TomoStack
        assert rec.data.shape[1] == slices.data.shape[2]

    def test_recon_sirt_gpu(self):
        stack = ds.get_needle_data(True)
        slices = stack.isig[:, 120:121].deepcopy()
        rec = slices.reconstruct('SIRT',
                                 constrain=True,
                                 iterations=2,
                                 thresh=0,
                                 cuda=True)
        assert type(stack) is tomotools.base.TomoStack
        assert type(rec) is tomotools.base.TomoStack
        assert rec.data.shape[1] == slices.data.shape[2]


@pytest.mark.skipif(not astra.use_cuda(), reason="CUDA not detected")
class TestAstraSIRTGPU:

    def test_astra_sirt_3d_data(self):
        stack = ds.get_needle_data(True)
        angles = stack.axes_manager[0].axis
        slices = stack.isig[:, 120:121].deepcopy().data
        rec = recon.astra_sirt(slices, angles,
                               thickness=None, iterations=2,
                               constrain=True, thresh=0, cuda=True)
        assert rec.shape == (1, slices.shape[2], slices.shape[2])
        assert rec.shape[0] == slices.shape[1]
        assert type(rec) is numpy.ndarray

    def test_astra_sirt_2d_data(self):
        stack = ds.get_needle_data(True)
        angles = stack.axes_manager[0].axis
        slices = stack.isig[:, 120].deepcopy().data
        rec = recon.astra_sirt(slices, angles,
                               thickness=None, iterations=2,
                               constrain=True, thresh=0, cuda=True)
        assert rec.shape == (1, slices.shape[1], slices.shape[1])
        assert rec.shape[0] == 1
        assert type(rec) is numpy.ndarray

    def test_astra_project_3d_data(self):
        stack = ds.get_needle_data(True)
        angles = stack.axes_manager[0].axis
        slices = stack.isig[:, 120:121].deepcopy().data
        rec = recon.astra_sirt(slices, angles,
                               thickness=None, iterations=1,
                               constrain=True, thresh=0, cuda=True)
        sino = recon.astra_project(rec, angles, cuda=True)
        assert sino.shape == (len(angles), rec.shape[0], rec.shape[2])
        assert sino.shape[1] == slices.shape[1]
        assert type(sino) is numpy.ndarray

    def test_astra_project_2d_data(self):
        stack = ds.get_needle_data(True)
        angles = stack.axes_manager[0].axis
        slices = stack.isig[:, 120].deepcopy().data
        rec = recon.astra_sirt(slices, angles,
                               thickness=None, iterations=1,
                               constrain=True, thresh=0, cuda=True)
        sino = recon.astra_project(rec, angles, cuda=True)
        assert sino.shape == (len(angles), rec.shape[0], rec.shape[2])
        assert sino.shape[1] == 1
        assert type(sino) is numpy.ndarray

    def test_astra_sirt_error_gpu(self):
        stack = ds.get_needle_data(True)
        angles = stack.axes_manager[0].axis
        slices = stack.isig[:, 120:121].deepcopy()
        rec_stack, error = recon.astra_sirt_error(slices, angles, iterations=10,
                                                  constrain=True, thresh=0, cuda=True)
        assert type(error) is numpy.ndarray


@pytest.mark.skipif(not astra.use_cuda(), reason="CUDA not detected")
class TestReconRunCUDA:
    def test_run_fbp_cuda(self):
        stack = ds.get_needle_data(True)
        slices = stack.isig[:, 120:121].deepcopy()
        rec = recon.run(slices, 'FBP', cuda=True)
        assert rec.data.shape == (1, slices.data.shape[2], slices.data.shape[2])
        assert rec.data.shape[0] == slices.data.shape[1]
        assert type(rec) is numpy.ndarray

    def test_run_sirt_cuda(self):
        stack = ds.get_needle_data(True)
        slices = stack.isig[:, 120:121].deepcopy()
        rec = recon.run(slices, 'SIRT', iterations=2, cuda=True)
        assert rec.data.shape == (1, slices.data.shape[2], slices.data.shape[2])
        assert rec.data.shape[0] == slices.data.shape[1]
        assert type(rec) is numpy.ndarray