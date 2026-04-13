"""
Market Simulator - The 'Time Machine'
Plays back historical CSV data as a live stream for training and testing
"""

import csv
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class MarketSimulator:
    """
    Simulates live market data by playing back historical CSV data
    Used for training AI on past market events and testing strategies
    """
    
    def __init__(self):
        self.data_cache: Dict[str, List[Dict]] = {}
        self.current_index: Dict[str, int] = {}
        self.playback_speed = 1.0  # 1.0 = real-time, 2.0 = 2x speed
        self.is_playing = False
        self.callbacks = []
    
    def load_csv(self, filepath: str, symbol: str) -> bool:
        """
        Load historical data from CSV file
        CSV format: timestamp, open, high, low, close, volume
        """
        try:
            data = []
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append({
                        'timestamp': float(row['timestamp']),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row.get('volume', 0))
                    })
            
            self.data_cache[symbol] = data
            self.current_index[symbol] = 0
            print(f"✅ Loaded {len(data)} data points for {symbol}")
            return True
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return False
    
    def generate_sample_csv(self, symbol: str, days: int = 30) -> str:
        """
        Generate a sample CSV file with simulated data for testing
        """
        filepath = f"data/{symbol}_sample.csv"
        os.makedirs('data', exist_ok=True)
        
        base_prices = {
            'EUR/USD': 1.0850,
            'AAPL': 150.0,
            'BTC/USD': 45000.0,
            'RELIANCE': 2500.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        data = []
        
        # Generate data points (1 per minute for testing)
        start_time = time.time() - (days * 24 * 60 * 60)
        current_price = base_price
        
        for i in range(days * 24 * 60):  # 1 minute intervals
            # Simulate price movement
            change = (hash(str(i)) % 100 - 50) / 10000 * base_price
            current_price += change
            
            # Generate OHLC
            open_price = current_price
            high_price = open_price + abs(change) * 0.5
            low_price = open_price - abs(change) * 0.5
            close_price = open_price + change * 0.3
            
            # Ensure high >= open, close and low <= open, close
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            data.append({
                'timestamp': start_time + i * 60,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': 1000 + (hash(str(i)) % 500)
            })
            
            current_price = close_price
        
        # Write to CSV
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ Generated sample CSV: {filepath}")
        return filepath
    
    def get_next_tick(self, symbol: str) -> Optional[Dict]:
        """
        Get the next data point for a symbol
        """
        if symbol not in self.data_cache:
            return None
        
        idx = self.current_index.get(symbol, 0)
        if idx >= len(self.data_cache[symbol]):
            return None
        
        data = self.data_cache[symbol][idx]
        self.current_index[symbol] = idx + 1
        return data
    
    def reset(self, symbol: str):
        """Reset playback to beginning for a symbol"""
        if symbol in self.current_index:
            self.current_index[symbol] = 0
    
    def get_current_data(self, symbol: str) -> Optional[Dict]:
        """
        Get current data point without advancing
        """
        if symbol not in self.data_cache:
            return None
        
        idx = self.current_index.get(symbol, 0)
        if idx >= len(self.data_cache[symbol]):
            return None
        
        return self.data_cache[symbol][idx]
    
    async def play(self, symbols: List[str], interval: float = 1.0):
        """
        Play back data for multiple symbols
        interval: seconds between ticks
        """
        self.is_playing = True
        
        while self.is_playing:
            tick_data = {}
            for symbol in symbols:
                data = self.get_next_tick(symbol)
                if data:
                    tick_data[symbol] = data
            
            if tick_data:
                # Notify callbacks
                for callback in self.callbacks:
                    await callback(tick_data)
            
            # Check if all symbols finished
            if all(self.current_index.get(s, 0) >= len(self.data_cache.get(s, [])) for s in symbols):
                print("✅ Playback completed")
                break
            
            await asyncio.sleep(interval / self.playback_speed)
    
    def stop(self):
        """Stop playback"""
        self.is_playing = False
    
    def add_callback(self, callback):
        """Add a callback function to receive tick data"""
        self.callbacks.append(callback)
    
    def get_progress(self, symbol: str) -> float:
        """Get playback progress as percentage"""
        if symbol not in self.data_cache:
            return 0.0
        
        total = len(self.data_cache[symbol])
        current = self.current_index.get(symbol, 0)
        return (current / total) * 100 if total > 0 else 0.0


# Example usage
if __name__ == "__main__":
    simulator = MarketSimulator()
    
    # Generate sample data
    print("Generating sample data...")
    simulator.generate_sample_csv('EUR/USD', days=7)
    
    # Load data
    simulator.load_csv('data/EUR/USD_sample.csv', 'EUR/USD')
    
    # Demo callback
    async def on_tick(data):
        for symbol, tick in data.items():
            print(f"{symbol}: {tick['close']:.2f} | Progress: {simulator.get_progress(symbol):.1f}%")
    
    simulator.add_callback(on_tick)
    
    # Play back at 10x speed
    simulator.playback_speed = 10.0
    print("Starting playback...")
    asyncio.run(simulator.play(['EUR/USD'], interval=0.1))
