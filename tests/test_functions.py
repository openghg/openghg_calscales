import pandas as pd
import pytest
import numpy as np

# from openghg_calscales import path
from openghg_calscales.functions import convert, _decimal_date, _split_explode, _synonyms
from openghg_calscales.util import path

scales_file = pd.read_csv(path("data/convert_functions.csv"),
                        comment="#").fillna("")


def scale_info(species, scale_1, scale_2):
    """Find the conversion function between two scales

    Args:
        species (str): Species
        scale_1 (str): Original scale
        scale_2 (str): Final scale

    Returns:
        str: Conversion function in convert_functions.csv
        bool: True if conversion from 1 to 2 in convert_functions.csv, False if 2 to 1
    """

    df = scales_file.copy()

    # Find rows where species is the same as the input species, scale_1 is in scale_x and scale_2 is in scale_y
    df = df[df["species"].str.lower() == _synonyms(species)]

    df = _split_explode(df, "scale_x")
    df = _split_explode(df, "scale_y")
    
    df_sub = df[(df["scale_x"].str.lower() == scale_1.lower()) & \
                  (df["scale_y"].str.lower() == scale_2.lower())]

    if len(df_sub) == 1:
        return df_sub["y=f(x)"].values[0], True
    
    elif len(df_sub) == 0:
        # Try searching the other way around
        df_sub = df[(df["scale_x"].str.lower() == scale_2.lower()) & \
                    (df["scale_y"].str.lower() == scale_1.lower())]
        
        if len(df_sub) == 1:
            return df_sub["y=f(x)"].values[0], False
        else:
            raise ValueError(f"No conversion found for {species} from {scale_1} to {scale_2} or vice versa")


def test_split_explode():
    """Test split_explode function"""

    df = pd.DataFrame({"a": ["a", "b", "c"], "b": ["d|e", "f", "g"]})

    df = _split_explode(df, "b")

    assert df.shape == (4, 2)
    assert df["b"].tolist() == ["d", "e", "f", "g"]

    # Test that an error will be thrown if the column doesn't exist
    with pytest.raises(KeyError):
        _split_explode(df, "c")


def test_decimal_date():
    """Test decimal_date function"""

    # Define a Timestamp
    t = pd.Timestamp('2022-07-15')

    # Calculate the decimal date
    result = _decimal_date(t)

    # Assert that the result is as expected
    # The expected result is calculated as 2022 + (196 / 365) because July 15 is the 196th day of the year
    expected = 2022 + (196 / 365)
    assert pytest.approx(result, 0.01) == expected


def test_synonyms():
    """Test synonyms function"""

    assert _synonyms("CFC-11") == "cfc11"
    assert _synonyms("cfc-11") == "cfc11"
    assert _synonyms("f11") == "cfc11"
    assert _synonyms("CH4") == "ch4"

    # Test that an error will be thrown if the species is not found
    with pytest.raises(ValueError):
        _synonyms("cfc-1222")


def test_scale_convert():
    """Test scale_convert function"""

    def test_series(time):
        return pd.Series([1.], index=pd.DatetimeIndex([time]))
    
    # Test a set of simple conversion factors
    tests_one_step = [("cfc-11", "SIO-93", "SIO-98"),
                    ("ch4", "CSIRO-94", "TU-87")]
    
    # Test a set of two step conversions
    # species, scale_start, scale_end, scale_intermediate
    tests_two_step = [("cfc-11", "SIO-93", "SIO-05", "SIO-98"),
                      ("ch3ccl3", "SIO-93", "SIO-05", "SIO-98")]
    
    # Test a set of reverse conversions
    tests_reverse = [("cfc-11", "SIO-98", "SIO-93"),
                     ("cfc-12", "SIO-05", "SIO-98")]
    
    for test in tests_one_step:
        df = test_series("1991-01-01")

        scale_function, direction = scale_info(test[0], test[1], test[2])

        assert float(scale_function.split("*")[0]) == convert(df, test[0], test[1], test[2]).values[0]

    for test in tests_two_step:
        df = test_series("1991-01-01")

        scale_function1, direction = scale_info(test[0], test[1], test[3])
        scale_function2, direction = scale_info(test[0], test[3], test[2])

        assert float(scale_function1.split("*")[0]) * float(scale_function2.split("*")[0]) == \
            convert(df, test[0], test[1], test[2]).values[0]

    # Test reverse conversions
    # Only works for simple scalings at the moment
    for test in tests_reverse:
        df = test_series("1991-01-01")

        scale_function, direction = scale_info(test[0], test[1], test[2])

        assert np.isclose(1./float(scale_function.split("*")[0]),
                          convert(df, test[0], test[1], test[2]).values[0],
                          rtol = 0.0001)

    # Test a conversion with a time component
    # Period where N2O time conversion applies
    assert np.isclose(convert(test_series("1985-01-01"), "n2o", "SIO-93", "SIO-98").values[0], 
        1.0058 * 0.9962230167482587, rtol = 0.0001)

    # Period where N2O time conversion applies (inverse of above)
    assert np.isclose(convert(test_series("1985-01-01"), "n2o", "SIO-98", "SIO-93").values[0],
        1./(1.0058 * 0.9962230167482587), rtol = 0.0001)

    # Period where N2O no time conversion applies
    assert np.isclose(convert(test_series("1980-01-01"), "n2o", "SIO-93", "SIO-98").values[0],
        1.0058, rtol = 0.0001)

    # Test that applying a conversion and then reversing gets us back to 1
    tests = [("cfc-11", "SIO-93", "SIO-05"),
             ("cfc-12", "SIO-05", "SIO-93"),
             ("ch4", "CSIRO-94", "TU-87"),
             ("n2o", "SIO-93", "SIO-98")]
        
    for test in tests:
        df = test_series("1991-01-01")

        df1 = convert(df, test[0], test[1], test[2])
        df2 = convert(df1, test[0], test[2], test[1])

        assert np.isclose(df.values[0], df2.values, rtol = 0.0001)

