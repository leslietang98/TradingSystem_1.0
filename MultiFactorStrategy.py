import backtrader as bt
import datetime
import numpy as np
import pandas as pd
import math

class MultiFactorStrategy(bt.Strategy):
    params = (
        ('assets', None),
        ('factors', None),
        ('hedge_pct', None)
    )
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.OrdinalToDatetime(float(self.datas[0].datetime[0]))
        print('%s, %s' % (dt.isoformat(" ","seconds"), txt))

    def __init__(self):
        self.assets = self.params.assets
        self.factors = self.params.factors
        self.hedge_pct = self.params.hedge_pct

        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.orefs = list()

    def notify_order(self, order):
        print('{}: Order ref: {} / Type {} / Status {}'.format(
            self.data.datetime.date(0),
            order.ref, 'Buy' * order.isbuy() or 'Sell',
            order.getstatusname()))

        # remove order from list after it has been filed
        if not order.alive() and order.ref in self.orefs:
            self.orefs.remove(order.ref)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def OrdinalToDatetime(self,ordinal):
        plaindate = datetime.date.fromordinal(int(ordinal))
        date_time = datetime.datetime.combine(plaindate, datetime.datetime.min.time())
        return date_time + datetime.timedelta(days=ordinal - int(ordinal))

    def signal_generation(self):
        pass

    def compute_overall_scores(self):
        # risk-parity, machine learning
        asset_factor_exposures_df = pd.DataFrame(index = self.assets,columns = self.factors)
        for asset in self.assets:
            for factor in self.factors:
                asset_factor_exposures_df.loc[asset][factor] = getattr(self.dnames[asset], factor)[0]

        # fill nan with average value, compute asset ranks according to factors
        asset_factor_exposures_df = asset_factor_exposures_df.apply(lambda x: x.fillna(x.mean()), axis=0)
        asset_factor_rank_df = asset_factor_exposures_df.rank(axis=0)

        # factor weighting (equal weight)
        self.asset_score_df = pd.DataFrame(asset_factor_rank_df.mean(axis = 1),columns = ["scores"])

    def compute_weights(self):
        # Mean weight
        # avg score = avg(long score + short score)
        # score - avg score / normalize
        asset_score_df = self.asset_score_df
        demeaned_score = asset_score_df["scores"].apply(lambda x:x-asset_score_df["scores"].mean(axis = 0))
        asset_weight_df = pd.DataFrame(demeaned_score/demeaned_score.abs().sum()).rename({"scores":"weights"},axis=1)

        # adjust weight for hedge percent
        asset_weight_df.sort_values(by=['weights'], inplace=True, ascending=False)
        asset_nums = int(np.floor(len(self.assets) * self.hedge_pct))

        self.long_assets = asset_weight_df[:asset_nums].index
        self.short_assets = asset_weight_df[-asset_nums:].index

        # Set left out asset weight to 0, re-normalize weights
        left_out_assets = [a for a in asset_weight_df.index if a not in (self.long_assets | self.short_assets)]
        asset_weight_df.loc[left_out_assets] = 0
        self.asset_weight_df = (asset_weight_df / asset_weight_df.abs().sum())

    def adjust_portfolio(self):
        # place rebalancing order according to weights
        asset_weight_df =self.asset_weight_df

        current_market_value = self.broker.getvalue()
        for asset in self.assets:
            target_percent = asset_weight_df["weights"].loc[asset]
            print(("{0} Order Target Percent: {1:.2%}").format(asset,target_percent))
            self.order = self.order_target_percent(data = self.getdatabyname(asset), target=target_percent)

        print("yes")


    def next(self):
        self.signal_generation()
        self.compute_overall_scores()
        self.compute_weights()
        self.adjust_portfolio()

