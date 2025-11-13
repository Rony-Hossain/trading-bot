"""
Log Retrieval Utility

Use this in a QuantConnect notebook or research environment to retrieve
and analyze logs from your live/paper trading algorithm.

Usage:
    from log_retrieval import LogRetriever

    retriever = LogRetriever(qb)  # qb = QuantConnect QuantBook
    logs = retriever.get_logs('2024-11-06')
    retriever.analyze_logs(logs)
    retriever.export_to_csv(logs, 'my_logs.csv')
"""

import json
import pandas as pd
from datetime import datetime, timedelta

class LogRetriever:
    """Retrieve and analyze logs from QuantConnect ObjectStore"""

    def __init__(self, qb):
        """
        Initialize with QuantBook instance

        Args:
            qb: QuantConnect QuantBook instance (from notebook)
        """
        self.qb = qb

    def list_available_logs(self):
        """List all available log files in ObjectStore"""
        try:
            # Get all keys from ObjectStore
            keys = self.qb.ObjectStore.GetKeys()

            # Filter for log files
            log_keys = [k for k in keys if k.startswith('logs_')]

            print(f"Found {len(log_keys)} log files:")
            for key in log_keys:
                print(f"  - {key}")

            return log_keys
        except Exception as e:
            print(f"Error listing logs: {e}")
            return []

    def get_logs(self, date_str, log_type='all'):
        """
        Retrieve logs for a specific date

        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            log_type: 'all', 'errors', 'trades', 'detections', 'performance'

        Returns:
            dict: Parsed log data
        """
        try:
            # Search for log file matching date
            date_key = date_str.replace('-', '')
            search_pattern = f"logs_{log_type}_*_{date_key}"

            # Get all keys and find match
            all_keys = self.qb.ObjectStore.GetKeys()
            matching_keys = [k for k in all_keys if date_key in k and f"logs_{log_type}" in k]

            if not matching_keys:
                print(f"No logs found for {date_str} with type '{log_type}'")
                return None

            # Use most recent if multiple matches
            key = matching_keys[-1]
            print(f"Retrieving logs from: {key}")

            # Get from ObjectStore
            json_str = self.qb.ObjectStore.Read(key)
            logs = json.loads(json_str)

            print(f"Successfully retrieved logs for {date_str}")
            return logs

        except Exception as e:
            print(f"Error retrieving logs: {e}")
            return None

    def get_date_range_logs(self, start_date, end_date, log_type='all'):
        """
        Retrieve logs for a date range

        Args:
            start_date: Start date string 'YYYY-MM-DD'
            end_date: End date string 'YYYY-MM-DD'
            log_type: Type of logs to retrieve

        Returns:
            dict: Combined log data
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        all_logs = {
            'logs': [],
            'errors': [],
            'trades': [],
            'detections': [],
            'performance': []
        }

        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            daily_logs = self.get_logs(date_str, log_type)

            if daily_logs:
                # Merge logs
                if 'logs' in daily_logs:
                    all_logs['logs'].extend(daily_logs['logs'])
                if 'errors' in daily_logs:
                    all_logs['errors'].extend(daily_logs['errors'])
                if 'trades' in daily_logs:
                    all_logs['trades'].extend(daily_logs['trades'])
                if 'detections' in daily_logs:
                    all_logs['detections'].extend(daily_logs['detections'])
                if 'performance' in daily_logs:
                    all_logs['performance'].extend(daily_logs['performance'])

            current += timedelta(days=1)

        return all_logs

    def analyze_logs(self, logs):
        """
        Generate analysis report from logs

        Args:
            logs: Log data dictionary

        Returns:
            dict: Analysis results with keys:
                - overall_stats: Session summary statistics
                - error_analysis: Error counts by component
                - trade_analysis: Trade statistics
                - detection_analysis: Extreme detection statistics
                - performance_trend: Portfolio performance metrics
        """
        if not logs:
            print("No logs to analyze")
            return None

        # Initialize analysis result
        analysis = {
            'overall_stats': {},
            'error_analysis': {},
            'trade_analysis': {},
            'detection_analysis': {},
            'performance_trend': {}
        }

        print("\n" + "="*60)
        print("LOG ANALYSIS REPORT")
        print("="*60 + "\n")

        # Overall stats
        if 'summary' in logs:
            summary = logs['summary']
            analysis['overall_stats'] = {
                'session_id': logs.get('session_id', 'N/A'),
                'total_logs': summary.get('total_logs', 0),
                'total_errors': summary.get('total_errors', 0),
                'total_trades': summary.get('total_trades', 0),
                'total_detections': summary.get('total_detections', 0)
            }

            print("Overall Stats:")
            print(f"  Session ID: {analysis['overall_stats']['session_id']}")
            print(f"  Total Logs: {analysis['overall_stats']['total_logs']}")
            print(f"  Total Errors: {analysis['overall_stats']['total_errors']}")
            print(f"  Total Trades: {analysis['overall_stats']['total_trades']}")
            print(f"  Total Detections: {analysis['overall_stats']['total_detections']}")
            print()

        # Error analysis
        if 'errors' in logs and logs['errors']:
            error_types = {}
            for error in logs['errors']:
                component = error.get('component', 'unknown')
                error_types[component] = error_types.get(component, 0) + 1

            analysis['error_analysis'] = {
                'by_component': error_types,
                'total_errors': len(logs['errors'])
            }

            print("Error Analysis:")
            for component, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {component}: {count} errors")
            print()

        # Trade analysis
        if 'trades' in logs and logs['trades']:
            trades = logs['trades']
            entry_count = sum(1 for t in trades if t['trade_type'] == 'entry')
            exit_count = sum(1 for t in trades if t['trade_type'] == 'exit')

            # Most traded symbols
            symbols = {}
            for trade in trades:
                sym = trade['symbol']
                symbols[sym] = symbols.get(sym, 0) + 1

            most_traded = sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:5]

            analysis['trade_analysis'] = {
                'total_trades': len(trades),
                'entries': entry_count,
                'exits': exit_count,
                'most_traded': most_traded
            }

            print("Trade Analysis:")
            print(f"  Total Trades: {len(trades)}")
            print(f"  Entries: {entry_count}")
            print(f"  Exits: {exit_count}")
            print(f"  Most traded: {most_traded}")
            print()

        # Detection analysis
        if 'detections' in logs and logs['detections']:
            detections = logs['detections']
            up = sum(1 for d in detections if d['direction'] == 'up')
            down = sum(1 for d in detections if d['direction'] == 'down')

            avg_z = sum(abs(d['z_score']) for d in detections) / len(detections)
            avg_vol = sum(d['vol_anomaly'] for d in detections) / len(detections)

            analysis['detection_analysis'] = {
                'total_extremes': len(detections),
                'up': up,
                'down': down,
                'avg_abs_z_score': avg_z,
                'avg_vol_anomaly': avg_vol
            }

            print("Detection Analysis:")
            print(f"  Total Extremes: {len(detections)}")
            print(f"  Up: {up}")
            print(f"  Down: {down}")
            print(f"  Avg |Z-score|: {avg_z:.2f}")
            print(f"  Avg Vol Anomaly: {avg_vol:.2f}x")
            print()

        # Performance trend
        if 'performance' in logs and logs['performance']:
            perf = logs['performance']

            if len(perf) >= 2:
                start_val = perf[0]['total_value']
                end_val = perf[-1]['total_value']
                change = ((end_val / start_val) - 1) * 100

                analysis['performance_trend'] = {
                    'snapshots': len(perf),
                    'start_value': start_val,
                    'end_value': end_val,
                    'percent_change': change
                }

                print("Performance Trend:")
                print(f"  Snapshots: {len(perf)}")
                print(f"  Start Value: ${start_val:,.2f}")
                print(f"  End Value: ${end_val:,.2f}")
                print(f"  Change: {change:+.2f}%")
            else:
                analysis['performance_trend'] = {
                    'snapshots': len(perf),
                    'insufficient_data': True
                }
                print("Performance Trend:")
                print(f"  Snapshots: {len(perf)} (insufficient for trend analysis)")
            print()

        print("="*60 + "\n")

        return analysis

    def export_to_csv(self, logs, filename_prefix='logs'):
        """
        Export logs to CSV files for external analysis

        Args:
            logs: Log data dictionary
            filename_prefix: Prefix for output files
        """
        if not logs:
            print("No logs to export")
            return

        # Export detections
        if 'detections' in logs and logs['detections']:
            df = pd.DataFrame(logs['detections'])
            filename = f"{filename_prefix}_detections.csv"
            df.to_csv(filename, index=False)
            print(f"Exported detections to {filename}")

        # Export trades
        if 'trades' in logs and logs['trades']:
            df = pd.DataFrame(logs['trades'])
            filename = f"{filename_prefix}_trades.csv"
            df.to_csv(filename, index=False)
            print(f"Exported trades to {filename}")

        # Export errors
        if 'errors' in logs and logs['errors']:
            df = pd.DataFrame(logs['errors'])
            filename = f"{filename_prefix}_errors.csv"
            df.to_csv(filename, index=False)
            print(f"Exported errors to {filename}")

        # Export performance
        if 'performance' in logs and logs['performance']:
            df = pd.DataFrame(logs['performance'])
            filename = f"{filename_prefix}_performance.csv"
            df.to_csv(filename, index=False)
            print(f"Exported performance to {filename}")

        print("Export complete!")

    def get_error_details(self, logs):
        """Get detailed error information"""
        if not logs or 'errors' not in logs:
            print("No errors found")
            return

        errors = logs['errors']

        print("\n" + "="*60)
        print("DETAILED ERROR REPORT")
        print("="*60 + "\n")

        for i, error in enumerate(errors[-20:], 1):  # Last 20 errors
            print(f"Error #{i}:")
            print(f"  Time: {error.get('timestamp', 'N/A')}")
            print(f"  Component: {error.get('component', 'unknown')}")
            print(f"  Level: {error.get('level', 'ERROR')}")
            print(f"  Message: {error.get('message', 'N/A')}")

            if 'exception' in error:
                exc = error['exception']
                print(f"  Exception: {exc.get('type', 'N/A')}: {exc.get('message', 'N/A')}")
                if 'traceback' in exc:
                    print(f"  Traceback:\n{exc['traceback']}")

            print()


# Example usage in QuantConnect Notebook:
"""
# In a QuantConnect Research Notebook

from log_retrieval import LogRetriever

# Initialize
qb = QuantBook()
retriever = LogRetriever(qb)

# List available logs
retriever.list_available_logs()

# Get logs for today
logs = retriever.get_logs('2024-11-06')

# Analyze
retriever.analyze_logs(logs)

# Export to CSV
retriever.export_to_csv(logs, 'extreme_aware_2024_11_06')

# Get specific date range
range_logs = retriever.get_date_range_logs('2024-11-01', '2024-11-06')
retriever.analyze_logs(range_logs)

# Detailed error report
retriever.get_error_details(logs)
"""
