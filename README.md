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

You can clone using ```git``` using:

```git clone ...```

Conda and pip installation coming soon.

## Usage

For example, to convert a Pandas Series or xarray DataArray from the CSIRO-94 to TU-87 scale for CH4:

```
from openghg_calscales import convert

ch4_tu1987 = convert(ch4_csiro94, "CH4", "CSIRO-94", "TU-1987")
```

Add your own functions to ```data/convert_functions.csv```, and submit them as a pull request to share with others.