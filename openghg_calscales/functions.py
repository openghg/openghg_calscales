import pandas as pd
import numpy as np
import networkx as nx
import xarray as xr
from sympy import sympify, symbols, solve, lambdify, Piecewise

from openghg_calscales.util import path


def _decimal_date(t):
    """Calculate decimalised date from datetimeindex

    Args:
        t (pd.DateTimeIndex): DatetimeIndex

    Returns:
        float: Decimalised date
    """
    # Check if t is a DatetimeIndex
    if not isinstance(t, pd.DatetimeIndex):
        try:
            t = pd.to_datetime(t)
        except:
            raise ValueError("t must be a pandas DatetimeIndex or a datetime object.")

    # Convert to decimalised date
    return t.year + t.dayofyear / (366 * t.is_leap_year + 365 * (~t.is_leap_year))


def _split_explode(data, column, sep="|"):
    """Split a Dataframe column into a list and explode into separate rows

    Args:
        data (pd.DataFrame): Dataframe
        column (str): Column to split

    Returns:
        pd.DataFrame: Dataframe with split column
    """

    # Split the synonyms into a list
    data[column] = data[column].apply(lambda x: str(x).split(sep))

    # Explode the list into separate rows
    data = data.explode(column, ignore_index=True)

    # Remove whitespace
    data[column] = data[column].apply(lambda x: x.strip())

    return data


def _synonyms(species):
    """Find synonyms for a species in species_synonyms.csv

    Args:
        species (str): Species

    Returns:
        str: Default name for species
    """

    syn = pd.read_csv(path("data/species_synonyms.csv"), comment="#").fillna("")

    syn = _split_explode(syn, "synonyms")

    # Find where "species" appears exactly in either the index or the "synonyms" column
    syn = syn[
        (syn["species"].str.lower() == species.lower()) | (syn["synonyms"].str.lower() == species.lower())
    ]
    syn = syn["species"].unique()

    if len(syn) != 1:
        raise ValueError(f"Could not find unique {species} in species_synonyms.csv")

    return syn[0]


def _scale_graph(species):
    """Build an directed graph from scale_convert.csv

    Args:
        species (str): Species

    Returns:
        nx.Graph: directed graph
    """

    data = pd.read_csv(path("data/convert_functions.csv"), comment="#").fillna("")

    # Remove any empty rows
    data = data[data["species"] != ""]

    # Filter for the specified species or synonyms (case insensitive)
    data = data[data["species"] == _synonyms(species.lower())]

    # synonyms are separated by a "|"
    # Split the synonyms into a list and explode
    for col in data.columns:
        data = _split_explode(data, col)

    # Replace index with a range
    data.index = range(len(data))

    # Construct graph
    G = nx.DiGraph()

    x, y, t = symbols("x y t")

    # Use sympy to construct equation from the "y=f(x)" column, and store its inverse in the "x=f(y)" column
    for i in range(len(data)):
        if data.iloc[i]["y=f(x)"]:
            # get function of x
            f = sympify(str(data.iloc[i]["y=f(x)"]))
            G.add_edge(data.iloc[i]["scale_x"].lower(), data.iloc[i]["scale_y"].lower(), f=f)
            # store the inverse function
            G.add_edge(
                data.iloc[i]["scale_y"].lower(),
                data.iloc[i]["scale_x"].lower(),
                f=(solve(f - y, x)[0]).subs(y, x),
            )

        elif data.iloc[i]["y=f(t)"]:
            # get function of t
            ft = sympify(str(data.iloc[i]["y=f(t)"]))

            if data.iloc[i]["t_start"]:
                # if there is a start date, function is f(t) between start and end dates
                t_start = float(data.iloc[i]["t_start"])
                t_end = float(data.iloc[i]["t_end"])
                t_else = sympify(str(data.iloc[i]["y=f(t)_else"]))
                f = Piecewise((ft, (t >= t_start) & (t <= t_end)), (t_else, True))

                G.add_edge(data.iloc[i]["scale_x"].lower(), data.iloc[i]["scale_y"].lower(), f=f)
                G.add_edge(data.iloc[i]["scale_y"].lower(), data.iloc[i]["scale_x"].lower(), f=1 / f)

            else:
                # No start or end dates, just use ft
                G.add_edge(data.iloc[i]["scale_x"].lower(), data.iloc[i]["scale_y"].lower(), f=ft)
                G.add_edge(data.iloc[i]["scale_y"].lower(), data.iloc[i]["scale_x"].lower(), f=1 / ft)

        else:
            raise ValueError(f"Row {i} needs to have either a function of x or t, none are present.")

    return G


def convert(c, species, scale_original, scale_new):
    """Convert mole fraction from one scale to another

    Args:
        c (pd.Series, xr.DataArray): Mole fraction timeseries
        species (str): Species
        scale_original (str): Original scale
        scale_new (str): New scale

    Returns:

    """
    # If no conversion required, return original dataset
    if scale_new is None:
        return c

    # If scales are the same, return original dataset
    if scale_original == scale_new:
        return c

    # Check that c is either a pandas Series or xarray dataarray
    if not isinstance(c, (pd.Series, xr.DataArray)):
        raise ValueError("Input must be a pandas Series or xarray DataArray.")

    # Check that c is not empty
    if len(c) == 0:
        return c

    # Check that c is not all NaNs
    if np.isnan(c).all():
        return c

    # Construct graph
    G = _scale_graph(species.lower())

    # Find the path and calculate the conversion factor
    x, t = symbols("x t")
    fx = sympify("x")
    ft = sympify("1")

    try:
        # Find shortest path through G and stitch together functions stored in f
        path = nx.shortest_path(G, source=scale_original.lower(), target=scale_new.lower())

        # Construct conversion function
        for i in range(len(path) - 1):
            f_edge = G[path[i]][path[i + 1]]["f"]

            if len(f_edge.free_symbols) > 1:
                raise ValueError(
                    f"Conversion function {f_edge} contains multiple inputs. Only one input is allowed at the moment"
                )

            # if x is in f_edge, substitute x with f_edge
            if x in f_edge.free_symbols:
                fx = fx.subs(x, f_edge)

            # if t is in f_edge, multiply ft by f_edge
            if t in f_edge.free_symbols:
                ft = ft * f_edge

    except nx.NetworkXNoPath:
        raise ValueError(f"No conversion path found between {scale_original} and {scale_new} for {species}.")

    # Apply the conversion function using sympy
    try:
        fn = lambdify((x, t), fx * ft, "numpy")
    except:
        raise ValueError(f"Conversion function {fx*ft} is not valid.")

    # Calculate decimal date
    if isinstance(c, pd.Series):
        dec_date = _decimal_date(c.index)
    elif isinstance(c, xr.DataArray):
        dec_date = _decimal_date(c.time.to_index())

    c_out = c.copy()
    c_out[:] = fn(c.values, dec_date)

    return c_out
