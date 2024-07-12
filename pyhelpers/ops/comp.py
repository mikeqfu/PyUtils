"""
Basic computation/conversion.
"""

import copy
import datetime
import math
import os
import re
import sys

import numpy as np
import pandas as pd


def gps_time_to_utc(gps_time):
    """
    Convert GPS time to UTC time.

    :param gps_time: Standard GPS time in seconds since GPS epoch (6 January 1980).
    :type gps_time: float
    :return: Corresponding UTC time.
    :rtype: datetime.datetime

    **Examples**::

        >>> from pyhelpers.ops import gps_time_to_utc
        >>> utc_dt = gps_time_to_utc(gps_time=1271398985.7822514)
        >>> utc_dt
        datetime.datetime(2020, 4, 20, 6, 23, 5, 782251)
    """

    gps_from_utc = (datetime.datetime(1980, 1, 6) - datetime.datetime(1970, 1, 1)).total_seconds()

    utc_time = datetime.datetime.utcfromtimestamp(gps_time + gps_from_utc)

    return utc_time


def parse_size(size, binary=True, precision=1):
    """
    Parse size into human-readable format or vice versa.

    :param size: Size to be parsed, either in human-readable format (e.g. ``'10 MB'``) or
        as an integer.
    :type size: str | int | float
    :param binary: Whether to use binary (factorised by 1024) or decimal (factorised by 10 ** 3)
        representation; defaults to ``True`` for binary representation.
    :type binary: bool
    :param precision: Number of decimal places when converting ``size`` to human-readable format;
        defaults to ``1``.
    :type precision: int
    :return: Parsed size, either as an integer (for machine-readable)
        or a formatted string (for human-readable).
    :rtype: int | str

    **Examples**::

        >>> from pyhelpers.ops import parse_size
        >>> parse_size(size='123.45 MB')
        129446707
        >>> parse_size(size='123.45 MB', binary=False)
        123450000
        >>> parse_size(size='123.45 MiB', binary=True)
        129446707
        >>> # If a metric unit (e.g. 'MiB') is specified in the input,
        >>> # the function returns a result accordingly, regardless of `binary`
        >>> parse_size(size='123.45 MiB', binary=False)
        129446707
        >>> parse_size(size=129446707, precision=2)
        '123.45 MiB'
        >>> parse_size(size=129446707, binary=False, precision=2)
        '129.45 MB'
    """

    min_unit, units_prefixes = 'B', ['K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    if binary is True:  # Binary system
        factor, units = 2 ** 10, [x + 'i' + min_unit for x in units_prefixes]
    else:  # Decimal (or metric) system
        factor, units = 10 ** 3, [x + min_unit for x in units_prefixes]

    if isinstance(size, str):
        val, sym = [x.strip() for x in size.split()]
        if re.match(r'.*i[Bb]', sym):
            factor, units = 2 ** 10, [x + 'i' + min_unit for x in units_prefixes]
        unit = [s for s in units if s[0] == sym[0].upper()][0]

        unit_dict = dict(zip(units, [factor ** i for i in range(1, len(units) + 1)]))
        parsed_size = int(float(val) * unit_dict[unit])  # in byte

    else:
        is_negative = size < 0
        temp_size, parsed_size = map(copy.copy, (abs(size), size))

        for unit in [min_unit] + units:
            if abs(temp_size) < factor:
                parsed_size = f"{'-' if is_negative else ''}{temp_size:.{precision}f} {unit}"
                break
            if unit != units[-1]:
                temp_size /= factor

    return parsed_size


def get_number_of_chunks(file_or_obj, chunk_size_limit=50, binary=True):
    """
    Get the total number of chunks of a data file, given a minimum chunk size limit.

    :param file_or_obj: Path to a file or an object representing the data.
    :type file_or_obj: typing.Any
    :param chunk_size_limit: Minimum limit of chunk size in megabytes (MB) or mebibytes (MiB)
        above which the function counts the number of chunks; defaults to ``50``.
    :type chunk_size_limit: int | float | None
    :param binary: Whether to use binary (factorised by 1024) or decimal (factorised by 10 ** 3)
        representation for size calculations; defaults to ``True`` for binary representation.
    :type binary: bool
    :return: Number of chunks, or ``None`` if ``file_or_obj`` is invalid
        or chunk calculation is not applicable.
    :rtype: int | None

    **Examples**::

        >>> from pyhelpers.ops import get_number_of_chunks
        >>> import numpy
        >>> example_obj = numpy.zeros((1000, 1000))
        >>> get_number_of_chunks(example_obj, chunk_size_limit=5)
        2
        >>> file_path = "C:\\Program Files\\Python310\\python310.pdb"
        >>> get_number_of_chunks(file_path, chunk_size_limit=2)
        8
    """

    factor = 2 ** 10 if binary is True else 10 ** 3

    if isinstance(file_or_obj, str) and os.path.exists(file_or_obj):
        size = os.path.getsize(file_or_obj)
    else:
        size = sys.getsizeof(file_or_obj)

    file_size_in_mb = round(size / (factor ** 2), 1)

    if chunk_size_limit:
        if file_size_in_mb > chunk_size_limit:
            number_of_chunks = math.ceil(file_size_in_mb / chunk_size_limit)
        else:
            number_of_chunks = 1
    else:
        number_of_chunks = None

    return number_of_chunks


def get_extreme_outlier_bounds(num_dat, k=1.5):
    # noinspection PyShadowingNames
    """
    Get the upper and lower bounds for extreme outliers using the interquartile range method.

    :param num_dat: Array-like object containing numerical data.
    :type num_dat: array-like
    :param k: Scale coefficient associated with the interquartile range; defaults to ``1.5``.
    :type k: float | int
    :return: Tuple containing the lower and upper bounds for extreme outliers.
    :rtype: tuple

    **Examples**::

        >>> from pyhelpers.ops import get_extreme_outlier_bounds
        >>> import pandas as pd
        >>> data = pd.DataFrame(range(100), columns=['col'])
        >>> data
            col
        0     0
        1     1
        2     2
        3     3
        4     4
        ..  ...
        95   95
        96   96
        97   97
        98   98
        99   99
        [100 rows x 1 columns]
        >>> data.describe()
                      col
        count  100.000000
        mean    49.500000
        std     29.011492
        min      0.000000
        25%     24.750000
        50%     49.500000
        75%     74.250000
        max     99.000000
        >>> lo_bound, up_bound = get_extreme_outlier_bounds(data, k=1.5)
        >>> lo_bound, up_bound
        (0.0, 148.5)
    """

    q1, q3 = np.percentile(num_dat, 25), np.percentile(num_dat, 75)
    iqr = q3 - q1

    lower_bound = np.max([0, q1 - k * iqr])
    upper_bound = q3 + k * iqr

    return lower_bound, upper_bound


def interquartile_range(num_dat):
    """
    Calculate the interquartile range (IQR) of numerical data.

    This function can serve as an alternative to
    `scipy.stats.iqr <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.iqr.html>`_.

    :param num_dat: Array-like object containing numerical data.
    :type num_dat: numpy.ndarray | list | tuple
    :return: Interquartile range of `num_dat`.
    :rtype: float

    **Examples**::

        >>> from pyhelpers.ops import interquartile_range
        >>> data = list(range(100))
        >>> iqr_result = interquartile_range(data)
        >>> iqr_result
        49.5
    """

    iqr = np.subtract(*np.percentile(num_dat, [75, 25]))

    return iqr


def find_closest_date(date, lookup_dates, as_datetime=False, fmt='%Y-%m-%d %H:%M:%S.%f'):
    """
    Find the closest date to a given date from a list of dates.

    :param date: Date to find the closest match for.
    :type date: str | datetime.datetime
    :param lookup_dates: Iterable of dates to search within.
    :type lookup_dates: typing.Iterable
    :param as_datetime: Whether to return the closest date as a datetime.datetime object;
        defaults to ``False`` which returns a string representation.
    :type as_datetime: bool
    :param fmt: Format string for datetime parsing and formatting;
        defaults to ``'%Y-%m-%d %H:%M:%S.%f'``.
    :type fmt: str
    :return: Closest date to the given `date`.
    :rtype: str | datetime.datetime

    **Examples**::

        >>> from pyhelpers.ops import find_closest_date
        >>> import pandas
        >>> example_dates = pandas.date_range('2019-01-02', '2019-12-31')
        >>> example_dates
        DatetimeIndex(['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-05',
                       '2019-01-06', '2019-01-07', '2019-01-08', '2019-01-09',
                       '2019-01-10', '2019-01-11',
                       ...
                       '2019-12-22', '2019-12-23', '2019-12-24', '2019-12-25',
                       '2019-12-26', '2019-12-27', '2019-12-28', '2019-12-29',
                       '2019-12-30', '2019-12-31'],
                      dtype='datetime64[ns]', length=364, freq='D')
        >>> example_date = '2019-01-01'
        >>> closest_example_date = find_closest_date(example_date, example_dates)
        >>> closest_example_date
        '2019-01-02 00:00:00.000000'
        >>> example_date = pandas.to_datetime('2019-01-01')
        >>> closest_example_date = find_closest_date(example_date, example_dates, as_datetime=True)
        >>> closest_example_date
        Timestamp('2019-01-02 00:00:00', freq='D')
    """

    closest_date = min(lookup_dates, key=lambda x: abs(pd.to_datetime(x) - pd.to_datetime(date)))

    if as_datetime:
        if isinstance(closest_date, str):
            closest_date = pd.to_datetime(closest_date)

    else:
        if isinstance(closest_date, datetime.datetime):
            closest_date = closest_date.strftime(fmt)

    return closest_date
