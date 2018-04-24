# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from hyperopt import hp
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class Quickie(IStrategy):
    """

    author@: Gert Wohlgemuth

    idea:
        momentum based strategie. The main idea is that it closes trades very quickly, while avoiding excessive losses. Hence a rather moderate stop loss in this case
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "60":  0.01,
        "30":  0.03,
        "20":  0.04,
        "0":  0.05
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.3

    # Optimal ticker interval for the strategy
    ticker_interval = 5

    def populate_indicators(self, dataframe: DataFrame) -> DataFrame:
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        dataframe['cci'] = ta.CCI(dataframe)
        dataframe['willr'] = ta.WILLR(dataframe)

        dataframe['smaSlow'] = ta.SMA(dataframe, timeperiod=7)
        dataframe['smaFast'] = ta.SMA(dataframe, timeperiod=13)

        # required for graphing
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']

        bollinger2 = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=1.5)
        dataframe['bb_lowerband_2'] = bollinger['lower']
        dataframe['bb_middleband_2'] = bollinger['mid']
        dataframe['bb_upperband_2'] = bollinger['upper']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                # we want to buy oversold assets
                (dataframe['cci'] <= -50)

                # some basic trend should have been established
                & (dataframe['macd'] > dataframe['macdsignal'])

                # which starts inside the band
                & (dataframe['open'] > dataframe['bb_lowerband'])
            )
            ,
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (dataframe['close'] >= dataframe['bb_upperband']) |
            (
                (dataframe['macd'] < dataframe['macdsignal']) &
                (dataframe['cci'] >= 100)
            )
            ,
            'sell'] = 1
        return dataframe
