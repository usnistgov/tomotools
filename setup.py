from distutils.core import setup

setup(
    name='TomoTools',
    version='0.1.0',
    author='Andrew A. Herzing',
    description='Suite of data processing algorithems for processing electron tomography data',
    long_description=open('README.txt').read(),
    install_requires=[
        "Hyperspy >= 1.0",
        "numpy",
        "scipy",
        "numpy",
        "os",
        "PyQt4",
        "collections",
        "warnings",
        "cv2",
        "copy",
        "matplotlib",
        "astra",
        "tqdm",
        "functools",
        "multiprocessing"
    ],
)