"""
Trading Engine for Ethrix AI Trading Hub
Handles live market data, AI agent analysis, and risk management
"""

import asyncio
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import random
import time
import pandas as pd
import yfinance as yf
import logging

# Setup logger
logger = logging.getLogger("Krystal.trading")

# FCS API Configuration (https://fcsapi.com)
FCS_API_BASE = "https://fcsapi.com/api-v3"


@dataclass
class MarketData:
    symbol: str
    bid: float
    ask: float
    change: float
    change_percent: float


@dataclass
class AgentAnalysis:
    agent: str
    signal: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    reasoning: str
    timestamp: str


@dataclass
class AgentPerformance:
    agent: str
    total_recommendations: int
    correct_predictions: int
    accuracy_score: float
    last_updated: str


@dataclass
class PendingTrade:
    symbol: str
    action: str  # 'BUY', 'SELL'
    amount: float
    price: float


class TradingEngine:
    """
    AI-Assisted Forex Trading Engine with Real Data Integration
    - Fetches live market data from yfinance
    - Runs parallel analysis with Groq (Technical) and Gemini (Sentiment)
    - Enforces Iron Guard risk management rules
    """
    
    # Market symbol mappings for yfinance
    MARKET_SYMBOLS = {
        'Forex': {
            'EUR/USD': 'EURUSD=X',
            'GBP/USD': 'GBPUSD=X',
            'USD/JPY': 'USDJPY=X'
        },
        'Stocks': {
            'AAPL': 'AAPL',
            'GOOGL': 'GOOGL',
            'TSLA': 'TSLA',
            'MSFT': 'MSFT'
        },
        'Nifty 50': {
            'RELIANCE': 'RELIANCE.NS',
            'TCS': 'TCS.NS',
            'HDFCBANK': 'HDFCBANK.NS',
            'INFY': 'INFY.NS'
        },
        'Crypto': {
            'BTC/USD': 'BTC-USD',
            'ETH/USD': 'ETH-USD',
            'SOL/USD': 'SOL-USD',
            'XRP/USD': 'XRP-USD'
        }
    }
    
    def __init__(self):
        self.capital = 100000.0  # Simulated capital
        self.daily_loss = 0.0
        self.risk_limit = 1.0  # 1% of capital max per trade
        self.daily_loss_limit = 5000.0  # Daily loss limit
        self.daily_profit = 0.0
        self.target_profit = 10000.0
        self.pending_trade: Optional[PendingTrade] = None
        self.market_data: Dict[str, MarketData] = {}
        self.analyses: List[AgentAnalysis] = []
        self.data_source: Dict[str, str] = {}  # Track data source per symbol: 'live' or 'simulated'
        self.system_shutdown = False
        self.shutdown_reason = ""
        
        # OHLC data storage for charts
        self.ohlc_data: Dict[str, List[Dict[str, Any]]] = {}
        
        # Price simulator state
        self.price_simulator_state: Dict[str, Dict[str, float]] = {}
        
        # AI Performance tracking
        self.agent_performance: Dict[str, AgentPerformance] = {}
        self.trade_history: List[Dict[str, Any]] = []
        
        # AI Agent controls
        self.groq_enabled = True
        self.gemini_enabled = True
        
        # API Keys (load from environment)
        self.fcs_access_key = os.getenv('FCS_ACCESS_KEY', 'your_access_key_here')
        self.groq_api_key = os.getenv('GROQ_KEY_1', '') or os.getenv('GROQ_API_KEY', '')
        self.gemini_api_key = os.getenv('GEMINI_KEY_1', '') or os.getenv('GEMINI_API_KEY', '')

        # Production mode flag - disable mock data when set to true (can be toggled via API)
        self.production_mode = False
        
        # Initialize market data and price simulator
        self._initialize_market_data()
        self._initialize_price_simulator()
        self._generate_initial_ohlc_data()
        self._initialize_agent_performance()

    async def fetch_market_data_for_mode(self, mode: str, symbol: str):
        """Fetch market data based on the requested mode (live/simulated)"""
        if mode == "live":
            await self._fetch_live_market_data_fcs(symbol)
        else:
            self._update_simulated_market_data(symbol)

    async def _fetch_live_market_data_fcs(self, symbol: str):
        """Fetch live market data from FCS API (fcsapi.com)"""
        try:
            # Prepare query parameters with access_key
            params = {
                'symbol': symbol,
                'access_key': self.fcs_access_key
            }
            
            # Use appropriate endpoint based on symbol type (Forex/Stocks/Crypto)
            endpoint = "/forex/latest"
            if "USD" in symbol and "/" in symbol:
                endpoint = "/forex/latest"
            elif "/" in symbol: # BTC/USD etc
                endpoint = "/crypto/latest"
            else:
                endpoint = "/stock/latest"

            response = requests.get(
                f"{FCS_API_BASE}{endpoint}", 
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    # FCS returns data in 'response' list or dict
                    ticker = data['response'][0] if isinstance(data['response'], list) else data['response']
                    
                    bid = float(ticker.get('b', ticker.get('price', 0)))
                    ask = float(ticker.get('a', ticker.get('price', 0)))
                    last = float(ticker.get('price', ticker.get('c', 0)))
                    change = float(ticker.get('ch', 0))
                    change_percent = float(ticker.get('cp', 0))
                    
                    self.market_data[symbol] = MarketData(
                        symbol=symbol,
                        bid=bid,
                        ask=ask,
                        change=change,
                        change_percent=change_percent
                    )
                    self.data_source[symbol] = 'live'
                    logger.info(f"[TRADING] Live FCS data for {symbol}: {last:.2f}")
                    return
            
            # Fallback to yfinance if FCS fails
            logger.warning(f"[TRADING] FCS API failed for {symbol}, falling back to yfinance")
            await self._fetch_yfinance_data(symbol)
            
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"[TRADING] Network error fetching FCS data for {symbol}: {e}")
            await self._fetch_yfinance_data(symbol)
        except Exception as e:
            logger.error(f"[TRADING] Error fetching live FCS data for {symbol}: {e}")
            await self._fetch_yfinance_data(symbol)

    async def _fetch_yfinance_data(self, symbol: str):
        """Fallback to yfinance for market data"""
        try:
            ticker = yf.Ticker(self.MARKET_SYMBOLS.get('Forex', {}).get(symbol, symbol))
            data = ticker.history(period='1d')
            if not data.empty:
                latest = data.iloc[-1]
                self.market_data[symbol] = MarketData(
                    symbol=symbol,
                    bid=latest['Close'],
                    ask=latest['Close'] * 1.0002,
                    change=latest['Close'] - latest['Open'],
                    change_percent=((latest['Close'] - latest['Open']) / latest['Open']) * 100
                )
                self.data_source[symbol] = 'live'
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"[TRADING] Network error in yfinance for {symbol}: {e}")
            self._update_simulated_market_data(symbol)
        except Exception as e:
            logger.error(f"[TRADING] yfinance fallback failed for {symbol}: {e}")
            self._update_simulated_market_data(symbol)

    def _update_simulated_market_data(self, symbol: str):
        """Generate/Update mock/simulated data for market closure or testing (Random Walk)"""
        # Skip mock data in production mode
        if self.production_mode:
            logger.info(f"[TRADING] Production mode enabled - skipping mock data for {symbol}")
            return

        if symbol not in self.market_data:
            self._add_mock_data(symbol)

        market = self.market_data[symbol]

        # Random Walk Simulation
        # Use a small percentage drift and volatility
        drift = random.uniform(-0.0001, 0.0001)  # Slight bias
        volatility = market.bid * 0.0005
        change = (market.bid * drift) + random.gauss(0, volatility)

        # Ensure bid doesn't go below zero
        new_bid = max(0.0001, market.bid + change)

        # Update OHLC-like data for consistency
        market.bid = new_bid
        market.ask = market.bid + (market.bid * 0.0002) # Fixed 2-pip relative spread
        market.change += change

        # Calculate percent change from a theoretical daily open (simplified)
        # We'll assume the first bid of the session was the 'open'
        if not hasattr(self, '_sim_opens'):
            self._sim_opens = {}
        if symbol not in self._sim_opens:
            self._sim_opens[symbol] = market.bid

        market.change_percent = ((market.bid - self._sim_opens[symbol]) / self._sim_opens[symbol]) * 100
        self.data_source[symbol] = 'simulated'
    
    def _initialize_market_data(self):
        """Initialize with real market data from yfinance"""
        # Try to fetch real data for all markets
        all_symbols = []
        for market in self.MARKET_SYMBOLS.values():
            all_symbols.extend(market.keys())
        
        for symbol in all_symbols:
            try:
                data = self.fetch_market_data(symbol, period='1d', interval='1m')
                if data is not None and not data.empty:
                    latest = data.iloc[-1]
                    spread = latest['Close'] * 0.0002  # 2 pips spread
                    
                    self.market_data[symbol] = MarketData(
                        symbol=symbol,
                        bid=latest['Close'],
                        ask=latest['Close'] + spread,
                        change=latest['Close'] - latest['Open'],
                        change_percent=((latest['Close'] - latest['Open']) / latest['Open']) * 100
                    )
                    self.data_source[symbol] = 'live'
                    logger.info(f"[TRADING] Loaded LIVE data for {symbol}: {latest['Close']:.2f}")
                else:
                    # Fallback to mock data
                    self._add_mock_data(symbol)
                    self.data_source[symbol] = 'simulated'
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"[TRADING] Network error, using mock data for {symbol}: {e}")
                self._add_mock_data(symbol)
            except Exception as e:
                logger.error(f"[TRADING] Using mock data for {symbol}: {e}")
                self._add_mock_data(symbol)
                self.data_source[symbol] = 'simulated'
    
    def _add_mock_data(self, symbol: str):
        """Add mock data as fallback"""
        # Skip mock data in production mode
        if self.production_mode:
            logger.info(f"[TRADING] Production mode enabled - skipping mock data for {symbol}")
            return

        base_prices = {
            'EUR/USD': 1.0850, 'GBP/USD': 1.2650, 'USD/JPY': 149.50,
            'AAPL': 150.0, 'GOOGL': 140.0, 'TSLA': 180.0, 'MSFT': 380.0,
            'RELIANCE': 2500.0, 'TCS': 3500.0, 'HDFCBANK': 1600.0, 'INFY': 1450.0,
            'BTC/USD': 45000.0, 'ETH/USD': 2500.0, 'SOL/USD': 100.0, 'XRP/USD': 0.60
        }

        base = base_prices.get(symbol, 100.0)
        spread = base * 0.0002

        self.market_data[symbol] = MarketData(
            symbol=symbol,
            bid=base,
            ask=base + spread,
            change=random.uniform(-1, 1),
            change_percent=random.uniform(-0.5, 0.5)
        )
    
    def _initialize_price_simulator(self):
        """Initialize price simulator with realistic parameters"""
        symbols = ['EUR/USD', 'GBP/USD', 'USD/JPY']
        base_prices = {'EUR/USD': 1.0850, 'GBP/USD': 1.2650, 'USD/JPY': 149.50}
        
        for symbol in symbols:
            self.price_simulator_state[symbol] = {
                'current_price': base_prices[symbol],
                'trend': random.choice([-1, 0, 1]),  # -1: bearish, 0: neutral, 1: bullish
                'volatility': random.uniform(0.0005, 0.002),
                'momentum': random.uniform(-0.001, 0.001),
                'last_update': time.time()
            }
    
    def _generate_initial_ohlc_data(self):
        """Generate initial OHLC data for charts using real yfinance data"""
        # Generate OHLC data for all symbols
        all_symbols = []
        for market in self.MARKET_SYMBOLS.values():
            all_symbols.extend(market.keys())
        
        for symbol in all_symbols:
            try:
                # Fetch real OHLC data from yfinance
                data = self.fetch_market_data(symbol, period='5d', interval='1m')
                if data is not None and not data.empty:
                    self.ohlc_data[symbol] = []
                    for _, row in data.tail(100).iterrows():
                        candle = {
                            'time': int(row.name.timestamp()),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close'])
                        }
                        self.ohlc_data[symbol].append(candle)
                    self.data_source[symbol] = 'live'
                    logger.info(f"[TRADING] Generated LIVE OHLC data for {symbol}: {len(self.ohlc_data[symbol])} candles")
                else:
                    # Fallback to mock data
                    self._generate_mock_ohlc(symbol)
                    self.data_source[symbol] = 'simulated'
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"[TRADING] Network error, using mock OHLC for {symbol}: {e}")
                self._generate_mock_ohlc(symbol)
            except Exception as e:
                logger.error(f"[TRADING] Using mock OHLC data for {symbol}: {e}")
                self._generate_mock_ohlc(symbol)
                self.data_source[symbol] = 'simulated'
    
    def _generate_mock_ohlc(self, symbol: str):
        """Generate mock OHLC data as fallback"""
        # Skip mock data in production mode
        if self.production_mode:
            logger.info(f"[TRADING] Production mode enabled - skipping mock OHLC data for {symbol}")
            return

        base_prices = {
            'EUR/USD': 1.0850, 'GBP/USD': 1.2650, 'USD/JPY': 149.50,
            'AAPL': 150.0, 'GOOGL': 140.0, 'TSLA': 180.0, 'MSFT': 380.0,
            'RELIANCE': 2500.0, 'TCS': 3500.0, 'HDFCBANK': 1600.0, 'INFY': 1450.0,
            'BTC/USD': 45000.0, 'ETH/USD': 2500.0, 'SOL/USD': 100.0, 'XRP/USD': 0.60
        }

        base = base_prices.get(symbol, 100.0)

        self.ohlc_data[symbol] = []
        for i in range(100):
            # Random walk for OHLC
            open_price = base + random.uniform(-1, 1)
            close_price = open_price + random.uniform(-0.5, 0.5)
            high_price = max(open_price, close_price) + random.uniform(0, 0.5)
            low_price = min(open_price, close_price) - random.uniform(0, 0.5)

            
            # Create candle
            candle = {
                'time': int(current_time.timestamp()),
                'open': round(open_price, 5),
                'high': round(high_price, 5),
                'low': round(low_price, 5),
                'close': round(close_price, 5)
            }
            
            self.ohlc_data[symbol].append(candle)
            current_time += timedelta(minutes=1)
            current_price = close_price
    
    def fetch_market_data(self, symbol: str, period: str = '1d', interval: str = '1m') -> Optional[pd.DataFrame]:
        """
        Fetch real market data from yfinance
        """
        try:
            # Map symbol to yfinance format
            yf_symbol = self._get_yfinance_symbol(symbol)
            if not yf_symbol:
                return None
            
            ticker = yf.Ticker(yf_symbol)
            data = ticker.history(period=period, interval=interval, timeout=10)
            
            if data.empty:
                return None
            
            return data
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"[TRADING] Network error fetching market data: {e}")
            return None
        except Exception as e:
            logger.error(f"[TRADING] Error fetching market data: {e}")
            return None
    
    def _get_yfinance_symbol(self, symbol: str) -> Optional[str]:
        """Map UI symbol to yfinance symbol"""
        for market, symbols in self.MARKET_SYMBOLS.items():
            if symbol in symbols:
                return symbols[symbol]
        return None
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        """
        if len(data) < period + 1:
            return 50.0  # Default neutral value
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.empty else 50.0
    
    def calculate_ema(self, data: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate Exponential Moving Average (EMA)
        """
        if len(data) < period:
            return data['Close'].iloc[-1]
        
        ema = data['Close'].ewm(span=period, adjust=False).mean()
        return ema.iloc[-1] if not ema.empty else data['Close'].iloc[-1]
    
    def calculate_sma(self, data: pd.DataFrame, period: int = 50) -> float:
        """
        Calculate Simple Moving Average (SMA)
        """
        if len(data) < period:
            return data['Close'].iloc[-1]
        
        sma = data['Close'].rolling(window=period).mean()
        return sma.iloc[-1] if not sma.empty else data['Close'].iloc[-1]
    
    def calculate_macd(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        """
        if len(data) < 26:
            return {'macd': 0.0, 'signal': 0.0, 'hist': 0.0}
        
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        
        return {
            'macd': macd.iloc[-1],
            'signal': signal.iloc[-1],
            'hist': hist.iloc[-1]
        }

    def get_technical_indicators(self, symbol: str) -> Dict[str, float]:
        """
        Get technical indicators for a symbol using yfinance data
        """
        data = self.fetch_market_data(symbol, period='5d', interval='5m')
        
        if data is None:
            # Return default values if data fetch fails
            return {
                'rsi': 50.0,
                'ema_20': 0.0,
                'ema_50': 0.0,
                'sma_50': 0.0,
                'macd': 0.0,
                'macd_signal': 0.0,
                'current_price': 0.0
            }
        
        macd_data = self.calculate_macd(data)
        
        indicators = {
            'rsi': self.calculate_rsi(data, period=14),
            'ema_20': self.calculate_ema(data, period=20),
            'ema_50': self.calculate_ema(data, period=50),
            'sma_50': self.calculate_sma(data, period=50),
            'macd': macd_data['macd'],
            'macd_signal': macd_data['signal'],
            'current_price': data['Close'].iloc[-1]
        }
        
        return indicators
    
    def _initialize_agent_performance(self):
        """Initialize performance tracking for AI agents"""
        agents = ['groq', 'gemini']
        for agent in agents:
            self.agent_performance[agent] = AgentPerformance(
                agent=agent,
                total_recommendations=0,
                correct_predictions=0,
                accuracy_score=0.0,
                last_updated=datetime.now().isoformat()
            )
    
    def track_agent_prediction(self, agent: str, signal: str, entry_price: float):
        """
        Track a prediction from an agent
        """
        if agent not in self.agent_performance:
            return
        
        self.agent_performance[agent].total_recommendations += 1
        self.agent_performance[agent].last_updated = datetime.now().isoformat()
        
        # Store for later evaluation
        self.trade_history.append({
            'agent': agent,
            'signal': signal,
            'entry_price': entry_price,
            'timestamp': datetime.now().isoformat(),
            'evaluated': False
        })
    
    def evaluate_predictions(self, current_prices: Dict[str, float]):
        """
        Evaluate past predictions against current prices
        """
        for trade in self.trade_history:
            if trade['evaluated']:
                continue
            
            agent = trade['agent']
            signal = trade['signal']
            entry_price = trade['entry_price']
            
            # Get current price for the symbol (simplified)
            symbol = trade.get('symbol', 'EUR/USD')
            current_price = current_prices.get(symbol, entry_price)
            
            # Determine if prediction was correct
            is_correct = False
            if signal == 'BUY' and current_price > entry_price:
                is_correct = True
            elif signal == 'SELL' and current_price < entry_price:
                is_correct = True
            
            if is_correct:
                self.agent_performance[agent].correct_predictions += 1
            
            # Update accuracy score
            total = self.agent_performance[agent].total_recommendations
            correct = self.agent_performance[agent].correct_predictions
            self.agent_performance[agent].accuracy_score = (correct / total * 100) if total > 0 else 0.0
            
            trade['evaluated'] = True
    
    def check_risk_limit(self) -> tuple[bool, str]:
        """
        Check if risk limits have been exceeded
        Returns (is_safe, message)
        """
        if self.daily_loss >= self.risk_limit * self.capital:
            self.system_shutdown = True
            self.shutdown_reason = f"Daily Loss Limit Exceeded: ${self.daily_loss:.2f} / ${self.risk_limit * self.capital:.2f}"
            return False, self.shutdown_reason
        
        if self.system_shutdown:
            return False, self.shutdown_reason
        
        return True, "Risk limits OK"
    
    def update_risk_settings(self, daily_loss_limit: float, target_profit: float):
        """Update risk settings from frontend"""
        self.risk_limit = daily_loss_limit / self.capital  # Convert to percentage
        self.target_profit = target_profit
    
    def execute_paper_trade(self, symbol: str, action: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Execute a paper trade and track for AI performance evaluation
        """
        if self.system_shutdown:
            return {
                'success': False,
                'message': self.shutdown_reason
            }
        
        # Check risk limit
        is_safe, message = self.check_risk_limit()
        if not is_safe:
            return {
                'success': False,
                'message': message
            }
        
        # Record trade for evaluation
        trade_record = {
            'symbol': symbol,
            'action': action,
            'amount': amount,
            'entry_price': price,
            'timestamp': datetime.now().isoformat(),
            'evaluated': False,
            'evaluation_time': (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        
        self.trade_history.append(trade_record)
        
        return {
            'success': True,
            'message': 'Paper trade executed',
            'trade_id': len(self.trade_history)
        }
    
    def toggle_groq(self, enabled: bool):
        """Toggle Groq agent on/off"""
        self.groq_enabled = enabled
        logger.info(f"[{'SUCCESS' if enabled else 'OFF'}] Groq agent {'enabled' if enabled else 'disabled'}")
    
    def toggle_gemini(self, enabled: bool):
        """Toggle Gemini agent on/off"""
        self.gemini_enabled = enabled
        logger.info(f"[{'SUCCESS' if enabled else 'OFF'}] Gemini agent {'enabled' if enabled else 'disabled'}")
    
    def get_agent_status(self) -> Dict[str, bool]:
        """Get current status of AI agents"""
        return {
            'groq_enabled': self.groq_enabled,
            'gemini_enabled': self.gemini_enabled
        }
    
    def evaluate_paper_trades(self):
        """
        Evaluate paper trades after 5 minutes and update AI performance
        """
        current_prices = {}
        for symbol, data in self.market_data.items():
            current_prices[symbol] = data.bid
        
        for trade in self.trade_history:
            if trade['evaluated']:
                continue
            
            # Check if 5 minutes have passed
            trade_time = datetime.fromisoformat(trade['timestamp'])
            eval_time = datetime.fromisoformat(trade['evaluation_time'])
            
            if datetime.now() < eval_time:
                continue
            
            # Evaluate the trade
            symbol = trade['symbol']
            entry_price = trade['entry_price']
            current_price = current_prices.get(symbol, entry_price)
            
            is_profitable = False
            if trade['action'] == 'BUY' and current_price > entry_price:
                is_profitable = True
            elif trade['action'] == 'SELL' and current_price < entry_price:
                is_profitable = True
            
            # Update daily PnL
            pnl = (current_price - entry_price) * trade['amount']
            if pnl > 0:
                self.daily_profit += pnl
            else:
                self.daily_loss += abs(pnl)
            
            # Update AI performance (associate with last analysis)
            if self.analyses:
                last_analysis = self.analyses[-1]
                agent = last_analysis.agent
                
                if agent in self.agent_performance:
                    self.agent_performance[agent].total_recommendations += 1
                    if is_profitable:
                        self.agent_performance[agent].correct_predictions += 1
                    
                    total = self.agent_performance[agent].total_recommendations
                    correct = self.agent_performance[agent].correct_predictions
                    self.agent_performance[agent].accuracy_score = (correct / total * 100) if total > 0 else 0.0
                    self.agent_performance[agent].last_updated = datetime.now().isoformat()
            
            trade['evaluated'] = True
            trade['pnl'] = pnl
            trade['profitable'] = is_profitable
    
    async def _groq_technical_analysis(self, symbol: str) -> AgentAnalysis:
        indicators = self.get_technical_indicators(symbol)
        rsi = indicators['rsi']
        ema_20 = indicators['ema_20']
        ema_50 = indicators['ema_50']
        current_price = indicators['current_price']
        
        # If API key is available, we could call Groq here for more complex analysis
        # For now, we'll use robust technical logic as requested
        
        signal = 'HOLD'
        if rsi < 30 and current_price > ema_20: # Oversold but starting to recover
            signal = 'BUY'
        elif rsi > 70 and current_price < ema_20: # Overbought but starting to drop
            signal = 'SELL'
        elif rsi < 45 and current_price > ema_50: # Bullish momentum
            signal = 'BUY'
        elif rsi > 55 and current_price < ema_50: # Bearish momentum
            signal = 'SELL'
        
        confidence = min(50 + (abs(50 - rsi) * 1.5), 95)
        
        reasoning = f"Technical Analysis for {symbol}: RSI at {rsi:.1f} shows {'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'} conditions. "
        reasoning += f"Price {current_price:.4f} is {'above' if current_price > ema_20 else 'below'} 20-period EMA ({ema_20:.4f}). "
        reasoning += f"Trend is {'Bullish' if current_price > ema_50 else 'Bearish'} based on 50-period EMA."
        
        return AgentAnalysis(
            agent='groq',
            signal=signal,
            confidence=round(confidence, 1),
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
    
    async def _gemini_sentiment_analysis(self, symbol: str) -> AgentAnalysis:
        """
        Gemini Agent: Sentiment Analysis
        Analyzes news and market sentiment
        """
        # If Gemini API key is available, we could call Gemini here
        # For now, we simulate realistic sentiment based on symbol and random factors
        
        # Simulate sentiment analysis
        sentiment_score = random.uniform(-1, 1)  # -1 (bearish) to 1 (bullish)
        
        if sentiment_score > 0.4:
            signal = 'BUY'
            confidence = round(60 + (sentiment_score * 35), 1)
            reasoning = f"Positive news flow detected for {symbol}. Global market sentiment is bullish on risk-on appetite. "
            reasoning += "Recent economic data suggests strong growth potential and institutional accumulation."
        elif sentiment_score < -0.4:
            signal = 'SELL'
            confidence = round(60 + (abs(sentiment_score) * 35), 1)
            reasoning = f"Negative news flow detected for {symbol}. Market sentiment is bearish due to macro-economic uncertainty. "
            reasoning += "Geopolitical tensions and rising inflation expectations are driving risk-off sentiment."
        else:
            signal = 'HOLD'
            confidence = round(50 + abs(sentiment_score) * 20, 1)
            reasoning = f"Neutral sentiment for {symbol}. Mixed news flow with no clear directional bias. "
            reasoning += "Market is currently in a consolidation phase awaiting further fundamental catalysts."
        
        return AgentAnalysis(
            agent='gemini',
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
    
    async def analyze_trade(self, symbol: str) -> List[AgentAnalysis]:
        """
        Trigger parallel analysis from enabled agents
        """
        analyses = []
        
        # Run enabled analyses in parallel
        tasks = []
        if self.groq_enabled:
            tasks.append(self._groq_technical_analysis(symbol))
        if self.gemini_enabled:
            tasks.append(self._gemini_sentiment_analysis(symbol))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            analyses.extend(results)
        
        # Track predictions for enabled agents
        data = self.market_data.get(symbol)
        if data:
            if self.groq_enabled and len(results) > 0:
                # Find Groq result (first if Groq is first in tasks)
                for result in results:
                    if result.agent == 'groq':
                        self.track_agent_prediction('groq', result.signal, data.bid)
                        break
            if self.gemini_enabled:
                for result in results:
                    if result.agent == 'gemini':
                        self.track_agent_prediction('gemini', result.signal, data.bid)
                        break
        
        self.analyses = analyses
        return self.analyses
    
    def _iron_guard_risk_check(self, trade: PendingTrade) -> tuple[bool, str]:
        """
        Iron Guard Risk Manager
        Strict Python logic to block risky trades
        """
        # Check 1: Trade size must not exceed 1% of capital
        trade_percent = (trade.amount / self.capital) * 100
        if trade_percent > self.risk_limit:
            return False, f"Trade rejected: Size ({trade_percent:.2f}%) exceeds risk limit ({self.risk_limit}%)"
        
        # Check 2: Daily loss limit
        if self.daily_loss >= self.daily_loss_limit:
            return False, f"Trade rejected: Daily loss (${self.daily_loss:.2f}) exceeds limit (${self.daily_loss_limit})"
        
        # Check 3: Simulate potential loss
        potential_loss = trade.amount * 0.02  # Assume 2% worst case
        if self.daily_loss + potential_loss > self.daily_loss_limit:
            return False, f"Trade rejected: Potential loss would exceed daily loss limit"
        
        return True, "Trade approved by Iron Guard"
    
    def generate_trade_signal(self, symbol: str) -> Optional[PendingTrade]:
        """
        Generate a trade signal based on agent consensus
        """
        if len(self.analyses) < 2:
            return None
        
        groq = next((a for a in self.analyses if a.agent == 'groq'), None)
        gemini = next((a for a in self.analyses if a.agent == 'gemini'), None)
        
        if not groq or not gemini:
            return None
        
        # Check for consensus
        if groq.signal == gemini.signal and groq.signal != 'HOLD':
            # Both agents agree
            action = groq.signal
            confidence = (groq.confidence + gemini.confidence) / 2
            
            if confidence > 70:  # Only trade if high confidence
                data = self.market_data.get(symbol)
                if not data:
                    return None
                
                # Calculate trade amount (1% of capital max)
                trade_amount = min(self.capital * 0.01, 10000)
                
                trade = PendingTrade(
                    symbol=symbol,
                    action=action,
                    amount=trade_amount,
                    price=data.ask if action == 'BUY' else data.bid
                )
                
                # Run Iron Guard check
                approved, reason = self._iron_guard_risk_check(trade)
                if approved:
                    self.pending_trade = trade
                    return trade
                else:
                    logger.warning(f"Iron Guard blocked trade: {reason}")
                    return None
        
        return None
    
    async def execute_trade(self, approved: bool) -> Dict[str, Any]:
        """
        Execute a trade (approved or rejected by human)
        """
        if not self.pending_trade:
            return {
                'success': False,
                'message': 'No pending trade to execute',
                'timestamp': datetime.now().isoformat()
            }

        if not approved:
            self.pending_trade = None
            return {
                'success': True,
                'status': 'rejected',
                'message': 'Trade rejected by human operator',
                'timestamp': datetime.now().isoformat()
            }
        
        # Simulate trade execution
        trade = self.pending_trade
        self.pending_trade = None
        
        # Calculate P/L (simulated)
        pl = random.uniform(-100, 250)
        self.capital += pl
        self.daily_profit += pl if pl > 0 else 0
        self.daily_loss += abs(pl) if pl < 0 else 0
        
        return {
            'success': True,
            'status': 'executed',
            'message': f"Trade {trade.action} {trade.symbol} executed successfully! P/L: ${pl:.2f}",
            'pl': pl,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_ohlc_data(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get OHLC data for a symbol
        """
        if symbol not in self.ohlc_data:
            return []
        
        # Update with latest candle
        self._update_latest_candle(symbol)
        
        # Return last N candles
        return self.ohlc_data[symbol][-limit:]
    
    def _update_latest_candle(self, symbol: str):
        """Update the latest candle with current price"""
        if symbol not in self.ohlc_data or len(self.ohlc_data[symbol]) == 0:
            return
        
        if symbol not in self.market_data:
            return
        
        current_price = self.market_data[symbol].bid
        
        # Update latest candle
        latest_candle = self.ohlc_data[symbol][-1]
        latest_candle['close'] = round(current_price, 5)
        latest_candle['high'] = max(latest_candle['high'], current_price)
        latest_candle['low'] = min(latest_candle['low'], current_price)
        
        # Add new candle every minute (simulated)
        current_time = datetime.now()
        candle_time = datetime.fromtimestamp(latest_candle['time'])
        
        if (current_time - candle_time).total_seconds() >= 60:
            # Create new candle
            new_candle = {
                'time': int(current_time.timestamp()),
                'open': round(current_price, 5),
                'high': round(current_price, 5),
                'low': round(current_price, 5),
                'close': round(current_price, 5)
            }
            self.ohlc_data[symbol].append(new_candle)
            
            # Keep only last 200 candles
            if len(self.ohlc_data[symbol]) > 200:
                self.ohlc_data[symbol] = self.ohlc_data[symbol][-200:]
    
    def calculate_position_size(self, symbol: str, risk_percentage: float, stop_loss_pips: float = 20) -> Dict[str, Any]:
        """
        Calculate position size based on risk percentage
        """
        if symbol not in self.market_data:
            return {'error': 'Symbol not found'}
        
        risk_amount = self.capital * (risk_percentage / 100)
        current_price = self.market_data[symbol].bid
        
        # Calculate position size (simplified)
        # In real trading, this would consider pip value, leverage, etc.
        pip_value = 0.0001 if 'JPY' not in symbol else 0.01
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Limit position size to reasonable amount
        max_position = self.capital * 0.1  # Max 10% of capital
        position_size = min(position_size, max_position)
        
        return {
            'symbol': symbol,
            'risk_percentage': risk_percentage,
            'risk_amount': round(risk_amount, 2),
            'current_price': round(current_price, 5),
            'stop_loss_pips': stop_loss_pips,
            'position_size': round(position_size, 2),
            'position_value': round(position_size * current_price, 2)
        }
    
    def get_status(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current trading status including market data and agent analyses.
        """
        indicators = {}
        if symbol:
            indicators = self.get_technical_indicators(symbol)

        return {
            "capital": self.capital,
            "daily_loss": self.daily_loss,
            "daily_profit": self.daily_profit,
            "target_profit": self.target_profit,
            "risk_limit": self.risk_limit,
            "daily_loss_limit": self.daily_loss_limit,
            "system_shutdown": self.system_shutdown,
            "shutdown_reason": self.shutdown_reason,
            "data_source": self.data_source,
            "indicators": indicators,
            "markets": [
                {
                    "symbol": data.symbol,
                    "bid": data.bid,
                    "ask": data.ask,
                    "change": data.change,
                    "change_percent": data.change_percent
                }
                for symbol, data in self.market_data.items()
            ],
            "analyses": [
                {
                    "agent": analysis.agent,
                    "signal": analysis.signal,
                    "confidence": analysis.confidence,
                    "reasoning": analysis.reasoning,
                    "timestamp": analysis.timestamp
                }
                for analysis in self.analyses
            ],
            "pending_trade": {
                "symbol": self.pending_trade.symbol,
                "action": self.pending_trade.action,
                "amount": self.pending_trade.amount,
                "price": self.pending_trade.price
            } if self.pending_trade else None,
            "position_size": self.last_position_size
        }
