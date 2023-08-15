# Synthesizing Verifiable Code for Large Specifications Using Few-Shot Learning - Accompanying code

This repo contains the source code as well as result csv's for Benedict Böttgers bachelor's thesis "Synthesizing Verifiable Code for Large Specifications Using Few-Shot Learning".

WIP

## Setup:
This was only tested on a Linux machine running Manjaro. It's strongly recommended to use WSL if you want to run this on Windows, otherwise the setup might be challenging.

- [Python 3.11.3](https://github.com/python/cpython) is used together with [Jupyter Notebooks](https://jupyter.org/install), which usually need to be installed separately
- [Syfco v1.2.1.2](https://github.com/reactive-systems/syfco) is required to be installed for most of the functionality.

### Synthesizing code
For synthesizing code using **Strix**, the binary is required to be in PATH (alternatively, the PATH can be specified in `strix.py` for a local installation).

**BoSy** currently relies on a docker image, so a working [Docker](https://www.docker.com) installation is required (as well as a running docker daemon).

Note that for most benchmarks the solutions have been pre-generated and are located in `./cache`, so the use of the tools might not be necessary in some cases.

### `verify.py`
To verify the verilog solutions there are several required binaries that need to be put into the PATH. This can either be done system-wide, or by changing the `path_dirs` variable in `verify.py`. These binaries are required to function (the versions are the one I used, but unless specified otherwise, older versions might work):
- [Yosys 0.25](https://github.com/YosysHQ/yosys)
- [Aiger-Tools 1.9.17](https://github.com/arminbiere/aiger) binaries
- Patched version of [combine-aiger](https://github.com/Pflyg/combine-aiger/tree/master)
- `ltl2smv` binary from [NuSMV](https://github.com/felipeblassioli/nusmv/tree/master). You need only the binary, which can be found separately, like from [here](https://github.com/hklarner/pyboolnet/tree/master/binaries)
- [NuXMV](https://nuxmv.fbk.eu) binary
- rename_single_vars.mjs (TODO)