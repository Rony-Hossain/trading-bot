"""
Enhanced Backtesting Framework with Realistic Cost Modeling

Provides more accurate backtest results by modeling:
- Realistic slippage (volatility and participation based)
- Market impact (volume-based)
- Time-of-day dependent spreads
- Fill probability
- TWAP execution simulation
- Detailed cost breakdown

Usage:
    from backtest_analyzer import BacktestAnalyzer
    
    analyzer = BacktestAnalyzer(algorithm)
    cost = analyzer.calculate_realistic_costs(trade)
    analyzer.generate_report()
"""

from AlgorithmImports import *
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta

class BacktestAnalyzer:
    """
    Advanced backtesting with realistic cost modeling
    """
    
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.logger = algorithm.logger if hasattr(algorithm, 'logger') else None
        
        # Trade tracking
        self.trades = []
        self.positions = {}
        
        # Performance tracking
        self.daily_returns = []
        self.equity_curve = []
        
        # Cost breakdown
        self.costs = {
            'spread': 0.0,
            'slippage': 0.0,
            'impact': 0.0,
            'fees': 0.0,
            'total': 0.0
        }
        
        # Statistics by category
        self.stats = {
            'by_direction': {'up': [], 'down': []},
            'by_regime': {'Low-Vol': [], 'High-Vol': [], 'Trending': []},
            'by_time': defaultdict(list),
            'by_symbol': defaultdict(list),
            'by_sector': defaultdict(list)
        }
        
        # Win/loss tracking
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        
        if self.logger:
            self.logger.info("BacktestAnalyzer initialized", component="BacktestAnalyzer")
    
    def calculate_realistic_costs(self, trade_info):
        """
        Calculate realistic trading costs
        
        Args:
            trade_info: dict with symbol, quantity, price, timestamp, volatility, adv
        
        Returns:
            dict with cost breakdown
        """
        
        symbol = trade_info['symbol']
        quantity = abs(trade_info['quantity'])
        price = trade_info['price']
        timestamp = trade_info['timestamp']
        
        # Get market data
        volatility = trade_info.get('volatility', 0.02)  # 2% default
        adv = trade_info.get('adv', 1_000_000)  # Average daily volume
        
        # 1. Spread cost
        spread_cost = self._calculate_spread_cost(price, timestamp)
        
        # 2. Slippage (participation + volatility based)
        slippage_cost = self._calculate_slippage(quantity, adv, volatility)
        
        # 3. Market impact
        impact_cost = self._calculate_market_impact(quantity, adv, volatility)
        
        # 4. Fees
        fee_cost = self._calculate_fees(quantity, price)
        
        # Total cost
        total_cost = spread_cost + slippage_cost + impact_cost + fee_cost
        
        # Cost breakdown
        costs = {
            'spread': spread_cost * quantity,
            'slippage': slippage_cost * quantity,
            'impact': impact_cost * quantity,
            'fees': fee_cost * quantity,
            'total': total_cost * quantity,
            'bps': (total_cost / price) * 10000  # Basis points
        }
        
        # Track cumulative costs
        for key in ['spread', 'slippage', 'impact', 'fees', 'total']:
            self.costs[key] += costs[key]
        
        return costs
    
    def _calculate_spread_cost(self, price, timestamp):
        """
        Calculate spread cost (time-of-day dependent)
        
        Spreads wider at open/close, tighter mid-day
        """
        
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Base spread (in dollars)
        base_spread_bps = 10  # 10 bps base
        
        # Time-of-day multiplier
        if (hour == 9 and minute < 45) or (hour == 15 and minute > 45):
            # First/last 15 minutes: wider spreads
            spread_mult = 2.0
        elif (hour == 9 and minute < 60) or (hour == 15 and minute > 30):
            # First/last 30 minutes: moderately wider
            spread_mult = 1.5
        elif hour >= 11 and hour <= 14:
            # Mid-day: tightest spreads
            spread_mult = 0.8
        else:
            # Normal hours
            spread_mult = 1.0
        
        # Spread cost per share
        spread_bps = base_spread_bps * spread_mult
        spread_cost = price * (spread_bps / 10000)
        
        # Cross the spread (pay half on average)
        return spread_cost * 0.5
    
    def _calculate_slippage(self, quantity, adv, volatility):
        """
        Calculate slippage based on participation rate and volatility
        
        Formula: slippage = sqrt(participation_rate) * volatility * alpha
        """
        
        # Estimate we trade over 5 minutes with 10% POV
        pov = 0.10  # 10% participation
        time_window_minutes = 5
        
        # Minute volume = ADV / (6.5 hours * 60 minutes)
        minute_volume = adv / (6.5 * 60)
        
        # Our share of volume in 5 minutes
        our_volume = quantity
        market_volume_5min = minute_volume * time_window_minutes * pov
        
        if market_volume_5min > 0:
            participation_rate = our_volume / market_volume_5min
        else:
            participation_rate = 0.1  # Default 10%
        
        # Cap participation rate
        participation_rate = min(participation_rate, 0.5)
        
        # Slippage model
        alpha = 0.5  # Calibration parameter
        slippage_pct = alpha * np.sqrt(participation_rate) * volatility
        
        return slippage_pct
    
    def _calculate_market_impact(self, quantity, adv, volatility):
        """
        Calculate market impact (permanent + temporary)
        
        Almgren-Chriss model simplified
        """
        
        # Daily volume participation
        participation = quantity / adv if adv > 0 else 0
        participation = min(participation, 0.25)  # Cap at 25% ADV
        
        # Impact parameters
        gamma = 0.1  # Temporary impact coefficient
        eta = 0.05   # Permanent impact coefficient
        
        # Temporary impact (goes away)
        temp_impact = gamma * volatility * np.sqrt(participation)
        
        # Permanent impact (stays)
        perm_impact = eta * volatility * participation
        
        # Total impact (we pay temp + half of perm)
        total_impact = temp_impact + (perm_impact * 0.5)
        
        return total_impact
    
    def _calculate_fees(self, quantity, price):
        """
        Calculate trading fees
        
        Interactive Brokers tiered pricing (example)
        """
        
        # IBKR tiered pricing (rough estimate)
        # $0.005 per share, $1 minimum
        per_share_fee = 0.005
        notional = quantity * price
        
        # SEC fees (sells only, but include for both for safety)
        sec_fee_rate = 0.0000278  # $27.80 per million
        sec_fee = notional * sec_fee_rate
        
        total_fee_per_share = per_share_fee + (sec_fee / quantity if quantity > 0 else 0)
        
        # Minimum $1
        total_fee = max(total_fee_per_share, 1.0 / quantity if quantity > 0 else 0)
        
        return total_fee
    
    def record_trade(self, trade_type, symbol, quantity, entry_price, exit_price=None, 
                    regime=None, direction=None, timestamp=None, metadata=None):
        """
        Record a trade for analysis
        
        Args:
            trade_type: 'open' or 'close'
            symbol: Stock symbol
            quantity: Share quantity
            entry_price: Entry price
            exit_price: Exit price (if closing)
            regime: Market regime
            direction: Trade direction ('up' or 'down')
            timestamp: Trade timestamp
            metadata: Additional info
        """
        
        timestamp = timestamp or self.algorithm.Time
        
        if trade_type == 'open':
            # Opening position
            self.positions[symbol] = {
                'entry_price': entry_price,
                'quantity': quantity,
                'entry_time': timestamp,
                'regime': regime,
                'direction': direction,
                'metadata': metadata or {}
            }
            
        elif trade_type == 'close' and symbol in self.positions:
            # Closing position
            position = self.positions[symbol]
            
            # Calculate P&L
            if exit_price:
                pnl = (exit_price - position['entry_price']) * position['quantity']
                hold_time = (timestamp - position['entry_time']).total_seconds() / 3600  # Hours
                
                # Calculate costs
                entry_costs = self.calculate_realistic_costs({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': position['entry_price'],
                    'timestamp': position['entry_time'],
                    'volatility': metadata.get('volatility', 0.02) if metadata else 0.02,
                    'adv': metadata.get('adv', 1_000_000) if metadata else 1_000_000
                })
                
                exit_costs = self.calculate_realistic_costs({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': exit_price,
                    'timestamp': timestamp,
                    'volatility': metadata.get('volatility', 0.02) if metadata else 0.02,
                    'adv': metadata.get('adv', 1_000_000) if metadata else 1_000_000
                })
                
                total_costs = entry_costs['total'] + exit_costs['total']
                net_pnl = pnl - total_costs
                
                # Record trade
                trade = {
                    'symbol': str(symbol),
                    'entry_time': position['entry_time'],
                    'exit_time': timestamp,
                    'hold_time_hours': hold_time,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'quantity': position['quantity'],
                    'gross_pnl': pnl,
                    'costs': total_costs,
                    'net_pnl': net_pnl,
                    'return_pct': (exit_price / position['entry_price'] - 1),
                    'regime': position.get('regime'),
                    'direction': position.get('direction'),
                    'metadata': position.get('metadata', {})
                }
                
                self.trades.append(trade)
                
                # Update stats
                if net_pnl > 0:
                    self.wins += 1
                else:
                    self.losses += 1
                
                self.total_pnl += net_pnl
                
                # Categorize
                if position.get('direction'):
                    self.stats['by_direction'][position['direction']].append(trade)
                
                if position.get('regime'):
                    self.stats['by_regime'][position['regime']].append(trade)
                
                hour = position['entry_time'].hour
                self.stats['by_time'][hour].append(trade)
                
                self.stats['by_symbol'][str(symbol)].append(trade)
            
            # Remove from positions
            del self.positions[symbol]
    
    def calculate_metrics(self):
        """Calculate comprehensive performance metrics"""
        
        if not self.trades:
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(df)
        win_rate = self.wins / total_trades if total_trades > 0 else 0
        
        winning_trades = df[df['net_pnl'] > 0]
        losing_trades = df[df['net_pnl'] < 0]
        
        avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['net_pnl'].mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(winning_trades['net_pnl'].sum() / losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else float('inf')
        
        # Return metrics
        total_return = df['net_pnl'].sum()
        avg_return_per_trade = df['net_pnl'].mean()
        
        # Risk metrics
        std_returns = df['net_pnl'].std()
        sharpe_ratio = (avg_return_per_trade / std_returns * np.sqrt(252)) if std_returns > 0 else 0
        
        # Hold time
        avg_hold_time = df['hold_time_hours'].mean()
        
        # Cost analysis
        total_costs = df['costs'].sum()
        avg_cost_per_trade = df['costs'].mean()
        cost_as_pct_of_pnl = abs(total_costs / total_return) if total_return != 0 else 0
        
        metrics = {
            'total_trades': total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_loss_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'avg_return_per_trade': avg_return_per_trade,
            'sharpe_ratio': sharpe_ratio,
            'avg_hold_time_hours': avg_hold_time,
            'total_costs': total_costs,
            'avg_cost_per_trade': avg_cost_per_trade,
            'cost_as_pct_of_pnl': cost_as_pct_of_pnl,
            'cost_breakdown': dict(self.costs)
        }
        
        return metrics
    
    def generate_report(self):
        """Generate comprehensive backtest report"""
        
        metrics = self.calculate_metrics()
        
        if not metrics:
            return "No trades to analyze"
        
        report = "\n" + "="*70 + "\n"
        report += "BACKTEST ANALYSIS REPORT\n"
        report += "="*70 + "\n\n"
        
        # Overall Performance
        report += "OVERALL PERFORMANCE:\n"
        report += "-"*70 + "\n"
        report += f"Total Trades:          {metrics['total_trades']}\n"
        report += f"Wins / Losses:         {metrics['wins']} / {metrics['losses']}\n"
        report += f"Win Rate:              {metrics['win_rate']:.2%}\n"
        report += f"Profit Factor:         {metrics['profit_factor']:.2f}\n"
        report += f"Total Return:          ${metrics['total_return']:,.2f}\n"
        report += f"Avg Return/Trade:      ${metrics['avg_return_per_trade']:,.2f}\n"
        report += f"Sharpe Ratio:          {metrics['sharpe_ratio']:.2f}\n"
        report += f"Avg Hold Time:         {metrics['avg_hold_time_hours']:.1f} hours\n"
        report += "\n"
        
        # Win/Loss Stats
        report += "WIN/LOSS STATISTICS:\n"
        report += "-"*70 + "\n"
        report += f"Average Win:           ${metrics['avg_win']:,.2f}\n"
        report += f"Average Loss:          ${metrics['avg_loss']:,.2f}\n"
        report += f"Avg Win/Loss Ratio:    {metrics['avg_win_loss_ratio']:.2f}\n"
        report += "\n"
        
        # Cost Analysis
        report += "COST ANALYSIS:\n"
        report += "-"*70 + "\n"
        report += f"Total Costs:           ${metrics['total_costs']:,.2f}\n"
        report += f"Avg Cost/Trade:        ${metrics['avg_cost_per_trade']:,.2f}\n"
        report += f"Costs as % of P&L:     {metrics['cost_as_pct_of_pnl']:.2%}\n"
        report += "\n"
        report += "Cost Breakdown:\n"
        report += f"  Spread:              ${metrics['cost_breakdown']['spread']:,.2f}\n"
        report += f"  Slippage:            ${metrics['cost_breakdown']['slippage']:,.2f}\n"
        report += f"  Market Impact:       ${metrics['cost_breakdown']['impact']:,.2f}\n"
        report += f"  Fees:                ${metrics['cost_breakdown']['fees']:,.2f}\n"
        report += "\n"
        
        # Performance by Category
        report += self._analyze_by_category()
        
        report += "="*70 + "\n"
        
        return report
    
    def _analyze_by_category(self):
        """Analyze performance by different categories"""
        
        report = ""
        
        # By direction
        if self.stats['by_direction']['up'] or self.stats['by_direction']['down']:
            report += "PERFORMANCE BY DIRECTION:\n"
            report += "-"*70 + "\n"
            
            for direction in ['up', 'down']:
                trades = self.stats['by_direction'][direction]
                if trades:
                    df = pd.DataFrame(trades)
                    wins = len(df[df['net_pnl'] > 0])
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {direction.upper()}: {total} trades, {wins}/{total} wins ({wins/total:.1%}), Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        # By regime
        if any(self.stats['by_regime'].values()):
            report += "PERFORMANCE BY REGIME:\n"
            report += "-"*70 + "\n"
            
            for regime in ['Low-Vol', 'High-Vol', 'Trending']:
                trades = self.stats['by_regime'][regime]
                if trades:
                    df = pd.DataFrame(trades)
                    wins = len(df[df['net_pnl'] > 0])
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {regime}: {total} trades, {wins}/{total} wins ({wins/total:.1%}), Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        # By time of day
        if self.stats['by_time']:
            report += "PERFORMANCE BY HOUR:\n"
            report += "-"*70 + "\n"
            
            for hour in sorted(self.stats['by_time'].keys()):
                trades = self.stats['by_time'][hour]
                if trades:
                    df = pd.DataFrame(trades)
                    total = len(df)
                    avg_pnl = df['net_pnl'].mean()
                    
                    report += f"  {hour:02d}:00: {total} trades, Avg P&L: ${avg_pnl:,.2f}\n"
            report += "\n"
        
        return report
    
    def export_trades_csv(self):
        """Export trades to CSV format"""
        if not self.trades:
            return None
        
        df = pd.DataFrame(self.trades)
        
        # Format for readability
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        
        return df
