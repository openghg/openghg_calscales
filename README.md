# OpenGHG gas calibration scale conversion tool

Convert from one calibration scale to another. If multiple conversions are required, conversion functions are chained together, following the shortest path.

Conversions can be defined as a function of the original scale, or as a function of time.

For example, conversion of CO from the WMO-X2014A to the CSIRO-94 scale uses a function: 

$$
\chi_{WMO} = (\chi_{CSIRO}+3.17)/0.9898
$$

Or the conversion of the SIO-93 to the SIO-98 scale for N$_2$O involves a 4th order polynomial as a function of time. 

The code uses ```sympy``` to rearrange the equations to do the conversion in the reverse order, or, in the case of time-based conversions, calculate the inverse. The shortest path between two scales is found using ```networkx```.

Please feel free to propose new scale conversions or bug fixes by submitting a pull request.

## Installation

### pip

You can install `openghg_calcscales` using `pip` 

```console
pip install openghg_calscales
```

### conda

Or with `conda` by doing

```console
conda install -c conda-forge -c openghg openghg_calscales
```

## Developer

If you want to make modifications to the package you can use an editable install with `pip`  


First, clone the repository using `git`

```console
git clone https://github.com/openghg/openghg_calscales.git
```

And then install the package using `pip`

```console
pip install -e openghg_calscales/
```

## Usage

For example, to convert a Pandas Series or xarray DataArray from the CSIRO-94 to TU-87 scale for CH4:

```python
from openghg_calscales import convert

ch4_tu1987 = convert(ch4_csiro94, "CH4", "CSIRO-94", "TU-1987")
```

Add your own functions to ```data/convert_functions.csv```, and submit them as a pull request to share with others.


## Development

For the recommended development process please see the [OpenGHG documentation](https://docs.openghg.org/development/python_devel.html)

### Release

The package is released using GitHub actions and pushed to conda and PyPI.

#### 1. Update the CHANGELOG

- Update the changelog to add the header for the new version and add the date. 
- Update the Unreleased header to match the version you're releasing and `...HEAD`.

#### 2. Update `pyproject.toml`

For a new release the package version must be updated in the `pyproject.toml` file. Try and follow the [Semantic Versioning](https://semver.org/) method.

#### 3. Tag the commit

Now tag the commit. First we create the tag and add a message (remember to insert correct version numbers here).

```console
git tag -a x.x.x -m "openghg_calscales release vx.x.x"
```

Next push the tag. This will trigger the automated release by GitHub Actions.

```console
git push origin x.x.x
```

#### 4. Check GitHub Actions runners

Check the GitHub Actions [runners](https://github.com/openghg/openghg_calscales/actions) to ensure the tests have
all passed and the build for conda and PyPI has run successfully.