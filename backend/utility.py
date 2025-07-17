# utils.py - Utility functions for the trading backend
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TradingUtils:
    """Utility class for trading operations"""
    
    @staticmethod
    def calculate_pnl(trades: List[Dict]) -> Dict:
        """Calculate PnL from trade history"""
        total_pnl = 0
        symbol_pnl = {}
        
        for trade in trades:
            symbol = trade['symbol']
            side = trade['side']
            quantity = float(trade['quantity'])
            price = float(trade['price'])
            
            if symbol not in symbol_pnl:
                symbol_pnl[symbol] = {'realized_pnl': 0, 'volume': 0}
            
            # Simple PnL calculation (buy low, sell high)
            if side == 'SELL':
                symbol_pnl[symbol]['realized_pnl'] += quantity * price
            else:
                symbol_pnl[symbol]['realized_pnl'] -= quantity * price
            
            symbol_pnl[symbol]['volume'] += quantity * price
        
        total_pnl = sum(data['realized_pnl'] for data in symbol_pnl.values())
        
        return {
            'total_pnl': round(total_pnl, 2),
            'symbol_breakdown': symbol_pnl
        }
    
    @staticmethod
    def validate_trading_pair(symbol: str) -> bool:
        """Validate if trading pair is supported"""
        supported_pairs = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
            'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT'
        ]
        return symbol.upper() in supported_pairs
    
    @staticmethod
    def calculate_position_size(balance: float, risk_percent: float, entry_price: float, stop_price: float) -> float:
        """Calculate position size based on risk management"""
        if stop_price >= entry_price:
            return 0
        
        risk_amount = balance * (risk_percent / 100)
        price_diff = entry_price - stop_price
        position_size = risk_amount / price_diff
        
        return round(position_size, 8)
    
    @staticmethod
    def format_price(price: float, symbol: str) -> str:
        """Format price based on symbol precision"""
        if 'USDT' in symbol:
            return f"{price:.2f}"
        else:
            return f"{price:.8f}"

# websocket_manager.py - WebSocket connection for real-time data
import asyncio
import json
import websockets
from typing import Callable

class BinanceWebSocketManager:
    """Manages WebSocket connections for real-time data"""
    
    def __init__(self):
        self.connections = {}
        self.callbacks = {}
    
    async def connect_ticker(self, symbol: str, callback: Callable):
        """Connect to ticker stream for real-time price updates"""
        stream_name = f"{symbol.lower()}@ticker"
        uri = f"wss://stream.binance.com:9443/ws/{stream_name}"
        
        try:
            async with websockets.connect(uri) as websocket:
                self.connections[symbol] = websocket
                self.callbacks[symbol] = callback
                
                async for message in websocket:
                    data = json.loads(message)
                    await callback(data)
                    
        except Exception as e:
            logger.error(f"WebSocket connection error for {symbol}: {e}")
    
    async def connect_kline(self, symbol: str, interval: str, callback: Callable):
        """Connect to kline/candlestick stream"""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        uri = f"wss://stream.binance.com:9443/ws/{stream_name}"
        
        try:
            async with websockets.connect(uri) as websocket:
                async for message in websocket:
                    data = json.loads(message)
                    await callback(data)
                    
        except Exception as e:
            logger.error(f"WebSocket kline connection error for {symbol}: {e}")
    
    def disconnect(self, symbol: str):
        """Disconnect WebSocket for a symbol"""
        if symbol in self.connections:
            self.connections[symbol].close()
            del self.connections[symbol]
            del self.callbacks[symbol]

# risk_manager.py - Risk management utilities
class RiskManager:
    """Risk management for trading operations"""
    
    def __init__(self, max_daily_loss: float = 1000, max_position_size: float = 0.1):
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        self.daily_pnl = 0
        self.positions = {}
    
    def can_place_order(self, symbol: str, side: str, quantity: float, price: float) -> tuple[bool, str]:
        """Check if order can be placed based on risk parameters"""
        
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            return False, "Daily loss limit exceeded"
        
        # Check position size limit
        position_value = quantity * price
        if position_value > self.max_position_size * 10000:  # Assuming 10k account
            return False, "Position size too large"
        
        # Check if position would exceed limits
        current_position = self.positions.get(symbol, 0)
        if side == 'BUY':
            new_position = current_position + quantity
        else:
            new_position = current_position - quantity
        
        if abs(new_position * price) > self.max_position_size * 10000:
            return False, "Position limit would be exceeded"
        
        return True, "Order approved"
    
    def update_position(self, symbol: str, side: str, quantity: float, price: float):
        """Update position after trade execution"""
        if symbol not in self.positions:
            self.positions[symbol] = 0
        
        if side == 'BUY':
            self.positions[symbol] += quantity
        else:
            self.positions[symbol] -= quantity
        
        # Update daily PnL (simplified)
        pnl_change = quantity * price if side == 'SELL' else -quantity * price
        self.daily_pnl += pnl_change
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        return {
            'daily_pnl': self.daily_pnl,
            'max_daily_loss': self.max_daily_loss,
            'positions': self.positions,
            'risk_utilization': abs(self.daily_pnl) / self.max_daily_loss * 100
        }

# Enhanced FastAPI endpoints (add to main.py)
from fastapi import BackgroundTasks

# Add these endpoints to your main FastAPI app

@app.get("/api/risk-metrics")
async def get_risk_metrics():
    """Get current risk management metrics"""
    # This would use your risk manager instance
    return {
        'daily_pnl': 150.25,
        'max_daily_loss': 1000,
        'risk_utilization': 15.02,
        'position_limits': {
            'max_position_size': 0.1,
            'current_exposure': 0.05
        }
    }

@app.get("/api/analytics")
async def get_analytics():
    """Get trading analytics and performance metrics"""
    try:
        client = get_binance_client()
        
        # Get account info
        account = client.get_account()
        
        # Calculate portfolio metrics
        total_balance = sum(float(b['free']) + float(b['locked']) for b in account['balances'])
        
        # Get recent performance
        trades = []
        for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
            try:
                recent_trades = client.get_my_trades(symbol=symbol, limit=50)
                trades.extend(recent_trades)
            except:
                continue
        
        # Calculate PnL
        pnl_data = TradingUtils.calculate_pnl(trades)
        
        return {
            'portfolio_value': total_balance,
            'total_pnl': pnl_data['total_pnl'],
            'win_rate': 65.4,  # Calculate from actual trades
            'sharpe_ratio': 1.23,  # Calculate from returns
            'max_drawdown': -2.5,
            'trades_count': len(trades),
            'symbol_breakdown': pnl_data['symbol_breakdown']
        }
    
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@app.post("/api/alerts")
async def create_price_alert(alert_data: dict):
    """Create price alert for a symbol"""
    # Implementation for price alerts
    return {
        'alert_id': 'alert_123',
        'symbol': alert_data['symbol'],
        'price': alert_data['price'],
        'condition': alert_data['condition'],
        'status': 'active'
    }

@app.get("/api/market-overview")
async def get_market_overview():
    """Get market overview with multiple symbols"""
    try:
        client = get_binance_client()
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
        market_data = []
        
        for symbol in symbols:
            try:
                ticker = client.get_ticker(symbol=symbol)
                market_data.append({
                    'symbol': symbol,
                    'price': float(ticker['lastPrice']),
                    'change': float(ticker['priceChangePercent']),
                    'volume': float(ticker['volume']),
                    'high': float(ticker['highPrice']),
                    'low': float(ticker['lowPrice'])
                })
            except:
                continue
        
        return market_data
    
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market overview")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time price updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send real-time price data
            # This would connect to Binance WebSocket streams
            await websocket.send_text(json.dumps({
                'symbol': symbol,
                'price': 41500.25,
                'timestamp': datetime.now().isoformat()
            }))
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()