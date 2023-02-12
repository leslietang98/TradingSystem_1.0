import backtrader as bt
import datetime
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame
from backtrader.feeds import PandasData

API_KEY = "PKKJ93QKOR85FQ4NO6WO"
API_SECRET = "WJGEeZKhmD7co2QYRHOo7IlED3RhmDgXBgeRREt4"
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_PAPER  = True

# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.OrdinalToDatetime(float(self.datas[0].datetime[0]))
        print('%s, %s' % (dt.isoformat(" ","seconds"), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        print("yes")
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

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

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1] * 0.95:
                # current close less than previous close

                if self.dataclose[-1] < self.dataclose[-2] * 0.95:
                    # previous close less than the previous close

                    # BUY, BUY, BUY!!! (with default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.buy()

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    def OrdinalToDatetime(self,ordinal):
        plaindate = datetime.date.fromordinal(int(ordinal))
        date_time = datetime.datetime.combine(plaindate, datetime.datetime.min.time())
        return date_time + datetime.timedelta(days=ordinal - int(ordinal))

class SmaCross(bt.SignalStrategy):
  def __init__(self):
    sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
    crossover = bt.ind.CrossOver(sma1, sma2)
    self.signal_add(bt.SIGNAL_LONG, crossover)

class Addmoredata(PandasData):
    #'openlast', 'closenext', 'AccNor_2', 'IdealRev', 'RetNor_2', 'Slope_2', 'TrendStrength', 'TurnoverReturn', 'VolatilityRatio', 'AbVol', 'PVcorr', 'OpenGap', 'RollYield_3', 'Seasonal', 'SFRR_3', 'LTMom_2', 'Stocks_2', 'WarrantChange', 'CapitalFlow', 'ShiborBeta'
    lines = ('AccNor_2', 'IdealRev', 'RetNor_2', 'Slope_2', 'TrendStrength', 'TurnoverReturn', 'VolatilityRatio')
    params = (('AccNor_2',2),('IdealRev',3),('RetNor_2',4),('Slope_2',5),('TrendStrength',6),('TurnoverReturn',7),('VolatilityRatio',8))

if __name__ == '__main__':
    # Create a cerebro entity
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    import pandas as pd
    import pickle

    test_data = pickle.load(open("save.p","rb"))

    asset_consize = {
        'A': 10.0, 'AG': 15.0, 'AL': 5.0, 'AU': 1000.0, 'C': 10.0,
        'CF': 5.0, 'CU': 5.0, 'FG': 20.0,
        'J': 100.0, 'JM': 60.0, 'L': 5.0, 'M': 10.0,
        'OI': 10.0, 'P': 10.0, 'RB': 10.0, 'RM': 10.0, 'RU': 10.0,
        'SR': 10.0, 'TA': 5.0, 'Y': 10.0, 'ZN': 5.0
    }
    transfeepct = 0.0005

    assets = [a for a in test_data.keys()]
    # no keys required for crypto data
    # client = StockHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)
    # # run_start = datetime.datetime(2023, 2, 6, 8, 30, tzinfo=pytz.timezone('US/Eastern'))
    # # run_end = datetime.datetime(2023, 2, 6, 10, 00, tzinfo=pytz.timezone('US/Eastern'))
    # run_start = datetime.datetime(2022, 2, 15, 8, 30)
    # run_end = datetime.datetime(2022, 3, 1, 10, 00)
    # request_params = StockBarsRequest(
    #     symbol_or_symbols=["AAPL"],
    #     timeframe=TimeFrame.Minute,
    #     start=run_start,
    #     end=run_end
    # )
    #
    # bars = client.get_stock_bars(request_params).df

    cerebro = bt.Cerebro()
    #comminfo = stampDutyCommissionScheme(stamp_duty=0.001, commission=0.0005)
    #cerebro.broker.addcommissioninfo(comminfo)
    # Add the Data Feed to Cerebro
    used_factors = ['AccNor_2', 'IdealRev', 'RetNor_2', 'Slope_2', 'TrendStrength', 'TurnoverReturn', 'VolatilityRatio']
    columns = ['open','close','AccNor_2', 'IdealRev', 'RetNor_2', 'Slope_2', 'TrendStrength', 'TurnoverReturn', 'VolatilityRatio']
    for asset in assets:
        feed = Addmoredata(dataname=pd.DataFrame(test_data[asset])[columns], plot=False,
                           fromdate=datetime.datetime(2015, 1, 1), todate=datetime.datetime(2021, 2, 1))
        cerebro.adddata(feed, name=asset)

    # Add a strategy
    from LeslieStrategy import LeslieStrategy
    from MultiFactorStrategy import MultiFactorStrategy

    cerebro.broker.setcommission(commission=0.0005)
    cerebro.addstrategy(MultiFactorStrategy, assets = assets,factors = used_factors,hedge_pct=0.5)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    cerebro.addsizer(bt.sizers.FixedSize,stake=100)
    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        timeframe = bt.dataseries.TimeFrame.Days,
        riskfreerate=0.02,
        _name='sharp_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything

    thestrats = cerebro.run()
    thestrat = thestrats[0]

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 输出分析器结果字典
    print('Sharpe Ratio:', thestrat.analyzers.sharp_ratio.get_analysis())
    print('DrawDown:', thestrat.analyzers.drawdown.get_analysis())

    # 进一步从字典中取出需要的值
    print('Sharpe Ratio:', thestrat.analyzers.sharp_ratio.get_analysis()['sharperatio'])
    print('Max DrawDown:', thestrat.analyzers.drawdown.get_analysis()['max']['drawdown'])

    # 打印各个分析器内容
    for a in thestrat.analyzers:
        a.print()
    cerebro.plot()
    print("yes")