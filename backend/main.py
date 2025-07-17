from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from binance.client import Client
from binance.exceptions import BinanceAPIException
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import uvicorn
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Binance Trading API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TradeRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    type: str  # MARKET or LIMIT
    quantity: str
    price: Optional[str] = None

class TradeResponse(BaseModel):
    orderId: str
    symbol: str
    status: str
    executedQty: str
    price: str

# Binance client initialization
def get_binance_client():
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    
    # Enhanced logging
    logger.info(f"Environment check - API Key exists: {api_key is not None}")
    logger.info(f"Environment check - Secret Key exists: {secret_key is not None}")
    
    if api_key:
        logger.info(f"API Key length: {len(api_key)}")
        logger.info(f"API Key starts with: {api_key[:5]}...")
    
    if secret_key:
        logger.info(f"Secret Key length: {len(secret_key)}")
        logger.info(f"Secret Key starts with: {secret_key[:5]}...")
    
    if not api_key or not secret_key:
        available_vars = [var for var in os.environ.keys() if 'BINANCE' in var.upper()]
        logger.error(f"Missing credentials. Available BINANCE vars: {available_vars}")
        logger.error(f"All environment variables: {list(os.environ.keys())}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Binance API credentials not configured. Available vars: {available_vars}"
        )
    
    try:
        client = Client(api_key, secret_key, testnet=False)
        # Test the connection
        ping_result = client.ping()
        logger.info(f"Binance client initialized successfully. Ping result: {ping_result}")
        return client
    except BinanceAPIException as e:
        logger.error(f"Binance API Exception during client initialization: {e}")
        logger.error(f"Error code: {getattr(e, 'code', 'unknown')}")
        logger.error(f"Error message: {getattr(e, 'message', 'unknown')}")
        raise HTTPException(status_code=500, detail=f"Binance API error: {e}")
    except Exception as e:
        logger.error(f"General exception during client initialization: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to connect to Binance API: {str(e)}")
    

@app.get("/")
async def root():
    return {"message": "Binance Trading API is running"}

@app.get("/api/balance")
async def get_balance():
    """Get account balance information"""
    try:
        client = get_binance_client()
        account_info = client.get_account()
        
        balances = []
        for balance in account_info['balances']:
            free_amount = float(balance['free'])
            locked_amount = float(balance['locked'])
            
            # Only include assets with non-zero balance
            if free_amount > 0 or locked_amount > 0:
                # Get USD value (simplified - you might want to implement proper price conversion)
                usd_value = 0
                if balance['asset'] == 'USDT':
                    usd_value = free_amount
                elif balance['asset'] in ['BTC', 'ETH', 'BNB']:
                    try:
                        ticker = client.get_symbol_ticker(symbol=f"{balance['asset']}USDT")
                        usd_value = free_amount * float(ticker['price'])
                    except Exception as ticker_error:
                        logger.warning(f"Could not get price for {balance['asset']}: {ticker_error}")
                        usd_value = 0
                
                balances.append({
                    'asset': balance['asset'],
                    'free': balance['free'],
                    'locked': balance['locked'],
                    'usdValue': round(usd_value, 2)
                })
        
        return balances
    
    except BinanceAPIException as e:
        logger.error(f"Binance API error in get_balance: {e}")
        raise HTTPException(status_code=400, detail=f"Binance API error: {e}")
    except Exception as e:
        logger.error(f"Error fetching balance: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch balance: {str(e)}")

@app.get("/api/market-overview")
async def get_market_overview():
    """Get market overview for multiple symbols"""
    try:
        client = get_binance_client()
        
        # Popular trading pairs
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT']
        market_data = []
        
        for symbol in symbols:
            try:
                # Get current price
                ticker = client.get_symbol_ticker(symbol=symbol)
                
                # Get 24hr price change
                price_change = client.get_ticker(symbol=symbol)
                
                market_data.append({
                    'symbol': symbol,
                    'price': f"{float(ticker['price']):,.2f}",
                    'change': f"{float(price_change['priceChangePercent']):+.2f}%",
                    'volume': f"{float(price_change['volume']):,.0f}",
                    'high': f"{float(price_change['highPrice']):,.2f}",
                    'low': f"{float(price_change['lowPrice']):,.2f}"
                })
            except Exception as symbol_error:
                logger.warning(f"Could not get data for {symbol}: {symbol_error}")
                continue
        
        return market_data
    
    except BinanceAPIException as e:
        logger.error(f"Binance API error in get_market_overview: {e}")
        raise HTTPException(status_code=400, detail=f"Binance API error: {e}")
    except Exception as e:
        logger.error(f"Error fetching market overview: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch market overview: {str(e)}")

@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a specific symbol"""
    try:
        client = get_binance_client()
        
        # Get current price
        ticker = client.get_symbol_ticker(symbol=symbol)
        
        # Get 24hr price change
        price_change = client.get_ticker(symbol=symbol)
        
        # Get recent klines for chart data
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=24)
        
        chart_data = []
        for kline in klines:
            chart_data.append({
                'time': datetime.fromtimestamp(kline[0] / 1000).strftime('%H:%M'),
                'price': float(kline[4])  # Close price
            })
        
        return {
            'symbol': symbol,
            'price': f"{float(ticker['price']):,.2f}",
            'change': f"{float(price_change['priceChangePercent']):+.2f}%",
            'volume': f"{float(price_change['volume']):,.0f}",
            'high': f"{float(price_change['highPrice']):,.2f}",
            'low': f"{float(price_change['lowPrice']):,.2f}",
            'chartData': chart_data
        }
    
    except BinanceAPIException as e:
        logger.error(f"Binance API error in get_market_data for {symbol}: {e}")
        raise HTTPException(status_code=400, detail=f"Binance API error: {e}")
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data for {symbol}: {str(e)}")

@app.post("/api/trade")
async def execute_trade(trade_request: TradeRequest):
    """Execute a trade order"""
    try:
        client = get_binance_client()
        
        # Validate trade request
        if trade_request.side not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Invalid side. Must be BUY or SELL")
        
        if trade_request.type not in ['MARKET', 'LIMIT']:
            raise HTTPException(status_code=400, detail="Invalid type. Must be MARKET or LIMIT")
        
        # Prepare order parameters
        order_params = {
            'symbol': trade_request.symbol,
            'side': trade_request.side,
            'type': trade_request.type,
            'quantity': trade_request.quantity,
        }
        
        # Add price for LIMIT orders
        if trade_request.type == 'LIMIT':
            if not trade_request.price:
                raise HTTPException(status_code=400, detail="Price is required for LIMIT orders")
            order_params['price'] = trade_request.price
            order_params['timeInForce'] = 'GTC'  # Good Till Canceled
        
        # Execute the order
        if trade_request.side == 'BUY':
            if trade_request.type == 'MARKET':
                order = client.order_market_buy(**order_params)
            else:
                order = client.order_limit_buy(**order_params)
        else:  # SELL
            if trade_request.type == 'MARKET':
                order = client.order_market_sell(**order_params)
            else:
                order = client.order_limit_sell(**order_params)
        
        return {
            'orderId': str(order['orderId']),
            'symbol': order['symbol'],
            'status': order['status'],
            'executedQty': order['executedQty'],
            'price': order.get('price', 'N/A'),
            'transactTime': order['transactTime']
        }
    
    except BinanceAPIException as e:
        logger.error(f"Binance API error in execute_trade: {e}")
        raise HTTPException(status_code=400, detail=f"Trade execution failed: {e}")
    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to execute trade: {str(e)}")

@app.get("/api/history")
async def get_trade_history():
    """Get recent trade history"""
    try:
        client = get_binance_client()
        
        # Get recent trades for major symbols
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        all_trades = []
        
        for symbol in symbols:
            try:
                trades = client.get_my_trades(symbol=symbol, limit=10)
                for trade in trades:
                    all_trades.append({
                        'id': trade['id'],
                        'symbol': trade['symbol'],
                        'side': 'BUY' if trade['isBuyer'] else 'SELL',
                        'quantity': trade['qty'],
                        'price': trade['price'],
                        'time': datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'FILLED'
                    })
            except Exception as trade_error:
                logger.warning(f"Could not get trades for {symbol}: {trade_error}")
                continue  # Skip if no trades for this symbol
        
        # Sort by time (most recent first)
        all_trades.sort(key=lambda x: x['time'], reverse=True)
        
        return all_trades[:20]  # Return last 20 trades
    
    except BinanceAPIException as e:
        logger.error(f"Binance API error in get_trade_history: {e}")
        raise HTTPException(status_code=400, detail=f"Binance API error: {e}")
    except Exception as e:
        logger.error(f"Error fetching trade history: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch trade history: {str(e)}")

@app.get("/api/orders/{symbol}")
async def get_open_orders(symbol: str):
    """Get open orders for a specific symbol"""
    try:
        client = get_binance_client()
        orders = client.get_open_orders(symbol=symbol)
        
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'orderId': str(order['orderId']),
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'quantity': order['origQty'],
                'price': order['price'],
                'status': order['status'],
                'time': datetime.fromtimestamp(order['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return formatted_orders
    
    except BinanceAPIException as e:
        logger.error(f"Binance API error in get_open_orders: {e}")
        raise HTTPException(status_code=400, detail=f"Binance API error: {e}")
    except Exception as e:
        logger.error(f"Error fetching open orders: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch open orders: {str(e)}")

@app.delete("/api/orders/{symbol}/{order_id}")
async def cancel_order(symbol: str, order_id: str):
    """Cancel an open order"""
    try:
        client = get_binance_client()
        result = client.cancel_order(symbol=symbol, orderId=order_id)
        
        return {
            'orderId': str(result['orderId']),
            'symbol': result['symbol'],
            'status': result['status'],
            'message': 'Order cancelled successfully'
        }
    
    except BinanceAPIException as e:
        logger.error(f"Binance API error in cancel_order: {e}")
        raise HTTPException(status_code=400, detail=f"Binance API error: {e}")
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed error reporting"""
    try:
        # Check environment variables first
        api_key = os.getenv("BINANCE_API_KEY")
        secret_key = os.getenv("BINANCE_SECRET_KEY")
        
        env_status = {
            "api_key_exists": api_key is not None,
            "secret_key_exists": secret_key is not None,
            "api_key_length": len(api_key) if api_key else 0,
            "secret_key_length": len(secret_key) if secret_key else 0
        }
        
        if not api_key or not secret_key:
            return {
                "status": "unhealthy", 
                "timestamp": datetime.now().isoformat(),
                "error": "Missing API credentials",
                "env_status": env_status,
                "available_env_vars": [var for var in os.environ.keys() if 'BINANCE' in var.upper()]
            }
        
        # Try to create client
        client = Client(api_key, secret_key, testnet=False)
        
        # Test the connection
        ping_result = client.ping()
        
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(), 
            "binance_connection": "ok",
            "env_status": env_status,
            "ping_result": ping_result
        }
        
    except BinanceAPIException as e:
        error_msg = f"Binance API Exception: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "unhealthy", 
            "timestamp": datetime.now().isoformat(),
            "error": error_msg,
            "error_type": "BinanceAPIException",
            "error_code": getattr(e, 'code', 'unknown')
        }
    except Exception as e:
        error_msg = f"General Exception: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {
            "status": "unhealthy", 
            "timestamp": datetime.now().isoformat(),
            "error": error_msg,
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "all_env_vars": list(os.environ.keys()),
        "binance_vars": {k: v[:10] + "..." if len(v) > 10 else v for k, v in os.environ.items() if 'BINANCE' in k.upper()},
        "api_key_exists": os.getenv("BINANCE_API_KEY") is not None,
        "secret_key_exists": os.getenv("BINANCE_SECRET_KEY") is not None
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))