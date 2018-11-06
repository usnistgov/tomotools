from setuptools import setup, find_packages

setup(
    name='tomotools',
    version='0.2.0',
    author='Andrew A. Herzing',
    description='Suite of data processing algorithms for processing electron tomography data',
    packages=find_packages(), install_requires=['numpy', 'qt', 'hyperspy', 'opencv', 'tqdm', 'matplotlib', 'tomopy',
                                                'astra-toolbox', 'scipy']
)
