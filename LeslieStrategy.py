import backtrader as bt
import datetime
import numpy
import pandas
import math
class LeslieStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.OrdinalToDatetime(float(self.datas[0].datetime[0]))
        print('%s, %s' % (dt.isoformat(" ","seconds"), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.orefs = list()

    def OrdinalToDatetime(self,ordinal):
        plaindate = datetime.date.fromordinal(int(ordinal))
        date_time = datetime.datetime.combine(plaindate, datetime.datetime.min.time())
        return date_time + datetime.timedelta(days=ordinal - int(ordinal))

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

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we hold any position
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1] * 0.999:
                # current close less than previous close

                if self.dataclose[-1] < self.dataclose[-2] * 0.999:
                    # previous close less than the previous close

                    # BUY, BUY, BUY!!! (with default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])

                    p1 = self.dataclose[0]
                    p2 = p1* 0.99
                    p3 = p1* 1.02

                    # Keep track of the created order to avoid a 2nd order
                    o1 = self.buy(exectype=bt.Order.Market,
                                  price=p1,
                                  transmit=False)

                    print('{}: Oref {} / Buy at {}'.format(
                        self.datetime.date(), o1.ref, p1))

                    o2 = self.sell(exectype=bt.Order.Stop,
                                   price=p2,
                                   parent=o1,
                                   transmit=False)

                    print('{}: Oref {} / Sell Limit at {}'.format(
                        self.datetime.date(), o2.ref, p2))

                    o3 = self.sell(exectype=bt.Order.Limit,
                                   price=p3,
                                   parent=o1,
                                   transmit=True)

                    print('{}: Oref {} / Sell Limit at {}'.format(
                        self.datetime.date(), o3.ref, p3))

                    self.orefs = [o1.ref,o2.ref, o3.ref]

        else:
            pass
            # Already in the market ... we might sell

            # if len(self) >= (self.bar_executed + 5):
            #     # SELL, SELL, SELL!!! (with all possible default parameters)
            #     self.log('SELL CREATE, %.2f' % self.dataclose[0])
            #
            #     # Keep track of the created order to avoid a 2nd order
            #     self.order = self.sell()