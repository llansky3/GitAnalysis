from datetime import datetime, timedelta, timezone
import requests
import pandas as pd

import numpy as np
from reliability.Distributions import Weibull_Distribution
from reliability.Probability_plotting import plot_points
import matplotlib.pyplot as plt
from reliability.Probability_plotting import plotting_positions


class Bugzilla:
    def __init__(self, host):
        self.host = host
        self.param_base = (
            "buglist.cgi?bug_status=UNCONFIRMED&bug_status=NEW"
            "&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=RESOLVED"
            "&bug_status=VERIFIED&bug_status=CLOSED&chfield=%5BBug%20creation%5D"
            "&chfieldfrom={date_from}&chfieldto={date_to}&columnlist=product%2Ccomponent%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Copendate&f1=version&o1=substring&product=Busybox&query_format=advanced&v1={version}"
        )

    def request(self, params: str) -> list[pd.DataFrame]:
        url = self.host + params
        resp = requests.get(url)
        return pd.read_html(resp.text)

    def fetch_bugs(
        self, _from: datetime, _to: datetime, version: str
    ) -> list[pd.DataFrame]:
        """
        Search for bugs in Bugzilla for a given period of time
        :param _from: search from date
        :param _to: search to date
        :param version: version of product
        """
        _from = str(_from.date())
        _to = str(_to.date())

        params = self.param_base.format(date_from=_from, date_to=_to, version=version)
        return self.request(params)


class CraftBench:
    def __init__(self, bugzilla: Bugzilla):
        self.bsc = bugzilla

    def transform_timestamp(self, stamp: str | datetime) -> float:
        dt = stamp
        if isinstance(stamp, str):
            try:
                dt = datetime.strptime(stamp, "%Y-%m-%d")
            except ValueError:
                # workaround @TODO
                dt = datetime.today()
        return dt.replace(tzinfo=timezone.utc).timestamp()

    def prepare_time_series(
        self, version: str, from_date: datetime, to_date: datetime, step_days
    ) -> list:
        time_series = []
        chunk = -1
        while True:
            chunk += 1
            _from = from_date - timedelta(days=step_days * chunk + step_days)
            _to = from_date - timedelta(days=step_days * chunk)

            if (_from - to_date).days <= 0:
                break
            try:
                fetched_bugs = self.bsc.fetch_bugs(
                    _from=_from, _to=_to, version=version
                )
            except Exception as ex:
                print("Failed to fetch data from Bugzilla:")
                print(ex)
                print(_from, _to)
                continue
            if not fetched_bugs:
                Exception("Failed to parse Bugzilla")

            bug_list = fetched_bugs[0]
            if bug_list.shape[0] == 0:
                break
            timestamps = [
                self.transform_timestamp(x) for x in bug_list.Opened.to_list()
            ]
            print(chunk, _from, timestamps)
            time_series.extend(timestamps)
        return sorted(time_series)

    def do_research(
        self, version: str, from_date: datetime, to_date: datetime, step_days=7
    ):
        data = self.prepare_time_series(
            version=version,
            from_date=from_date,
            to_date=to_date,
            step_days=step_days,
        )
        to_date_ts = self.transform_timestamp(to_date)
        normalized = [x - to_date_ts for x in data]
        # plotting positions
        t, F = plotting_positions(failures=normalized)
        print("t =", t)
        print("F =", F)

        # forward transform
        x = np.log(t)
        y = np.log(-np.log(1 - F))
        m, c = np.polyfit(x, y, 1)
        print("m =", m)
        print("c =", c)

        # reverse transform
        beta = m
        alpha = np.exp(-c / beta)
        print("alpha =", alpha)
        print("beta =", beta)

        plot_points(failures=normalized, marker="o")
        Weibull_Distribution(alpha=alpha, beta=beta).CDF()
        plt.show()


if __name__ == "__main__":
    """
    From Busybox's mainpage, the releases and their dates are the following:

    3 January 2023 -- BusyBox 1.36.0
    26 December 2021 -- BusyBox 1.35.0
    30 November 2021 -- BusyBox 1.33.2
    30 September 2021 -- BusyBox 1.34.1
    19 August 2021 -- BusyBox 1.34.0
    3 May 2021 -- BusyBox 1.33.1
    1 January 2021 -- BusyBox 1.32.1
    29 December 2020 -- BusyBox 1.33.0
    26 June 2020 -- BusyBox 1.32.0
    25 October 2019 -- BusyBox 1.31.1
    10 June 2019 -- BusyBox 1.31.0
    14 February 2019 -- BusyBox 1.30.1
    31 December 2018 -- BusyBox 1.30.0
    9 September 2018 -- BusyBox 1.29.3
    31 July 2018 -- BusyBox 1.29.2
    15 July 2018 -- BusyBox 1.29.1
    1 July 2018 -- BusyBox 1.29.0
    22 May 2018 -- BusyBox 1.28.4
    3 April 2018 -- BusyBox 1.28.3
    26 March 2018 -- BusyBox 1.28.2
    15 February 2018 -- BusyBox 1.28.1
    2 January 2018 -- BusyBox 1.28.0
    17 August 2017 -- BusyBox 1.27.2
    18 July 2017 -- BusyBox 1.27.1
    3 July 2017 -- BusyBox 1.27.0
    10 January 2017 -- BusyBox 1.26.2
    2 January 2017 -- BusyBox 1.26.1
    20 December 2016 -- BusyBox 1.26.0
    7 October 2016 -- BusyBox 1.25.1
    22 June 2016 -- BusyBox 1.25.0
    24 March 2016 -- BusyBox 1.24.2
    24 October 2015 -- BusyBox 1.24.1
    12 October 2015 -- BusyBox 1.24.0
    23 March 2015 -- BusyBox 1.23.2
    27 January 2015 -- BusyBox 1.23.1
    23 December 2014 -- BusyBox 1.23.0
    20 January 2014 -- BusyBox 1.22.1
    1 January 2014 -- BusyBox 1.22.0
    29 June 2013 -- BusyBox 1.21.1
    21 January 2013 -- BusyBox 1.21.0
    2 July 2012 -- BusyBox 1.20.2
    """
    bugzilla = Bugzilla(host="https://bugs.busybox.net/")
    bench = CraftBench(bugzilla=bugzilla)
    # we take release date of 1.35 and put feed it to the craft bench
    bench.do_research(
        version="1.35",
        from_date=datetime.today(),
        to_date=datetime.strptime("26 December 2021", "%d %B %Y"),
    )
