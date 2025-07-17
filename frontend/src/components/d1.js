import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, Wallet, Activity, DollarSign } from 'lucide-react';

// Mock data for demonstration
const mockBalances = [
  { asset: 'BTC', free: '0.05234', locked: '0.00000', usdValue: 2156.78 },
  { asset: 'ETH', free: '1.2345', locked: '0.0000', usdValue: 2839.21 },
  { asset: 'USDT', free: '1250.00', locked: '0.00', usdValue: 1250.00 },
  { asset: 'BNB', free: '5.678', locked: '0.000', usdValue: 1701.23 }
];

const mockPriceData = [
  { time: '09:00', price: 41200 },
  { time: '10:00', price: 41350 },
  { time: '11:00', price: 41180 },
  { time: '12:00', price: 41420 },
  { time: '13:00', price: 41380 },
  { time: '14:00', price: 41560 },
  { time: '15:00', price: 41490 }
];

const mockTradeHistory = [
  { id: 1, symbol: 'BTCUSDT', side: 'BUY', quantity: '0.001', price: '41200', time: '2024-01-15 14:30:00', status: 'FILLED' },
  { id: 2, symbol: 'ETHUSDT', side: 'SELL', quantity: '0.1', price: '2850', time: '2024-01-15 13:45:00', status: 'FILLED' },
  { id: 3, symbol: 'BTCUSDT', side: 'BUY', quantity: '0.002', price: '41350', time: '2024-01-15 12:15:00', status: 'FILLED' }
];

const Dashboard = () => {
  const [balances, setBalances] = useState(mockBalances);
  const [currentPrice, setCurrentPrice] = useState({ symbol: 'BTCUSDT', price: '41,485.20', change: '+2.35%' });
  const [priceData] = useState(mockPriceData);
  const [tradeHistory, setTradeHistory] = useState(mockTradeHistory);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [tradeForm, setTradeForm] = useState({
    symbol: 'BTCUSDT',
    side: 'BUY',
    type: 'MARKET',
    quantity: '',
    price: ''
  });
  const [loading, setLoading] = useState(false);

  // Removed API calls for now - using mock data only
  const fetchBalances = () => {
    setBalances(mockBalances);
  };

  const fetchMarketData = (symbol) => {
    setCurrentPrice({ symbol: symbol, price: '41,485.20', change: '+2.35%' });
  };

  const executeTrade = () => {
    if (!tradeForm.quantity || (tradeForm.type === 'LIMIT' && !tradeForm.price)) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      console.log('Trade executed:', tradeForm);
      alert('Trade executed successfully!');
      setTradeForm({ ...tradeForm, quantity: '', price: '' });
      
      // Add to trade history
      const newTrade = {
        id: tradeHistory.length + 1,
        symbol: tradeForm.symbol,
        side: tradeForm.side,
        quantity: tradeForm.quantity,
        price: tradeForm.price || '41485',
        time: new Date().toLocaleString(),
        status: 'FILLED'
      };
      setTradeHistory([newTrade, ...tradeHistory]);
      
      setLoading(false);
    }, 1000);
  };

  const fetchTradeHistory = () => {
    setTradeHistory(mockTradeHistory);
  };

  useEffect(() => {
    fetchBalances();
    fetchMarketData(selectedSymbol);
    fetchTradeHistory();
  }, [selectedSymbol]);

  const totalPortfolioValue = balances.reduce((sum, balance) => sum + balance.usdValue, 0);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Binance Trading Dashboard</h1>
          <p className="text-gray-400">Real-time trading and portfolio management</p>
        </div>

        {/* Portfolio Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Portfolio Value</p>
                <p className="text-2xl font-bold">${totalPortfolioValue.toLocaleString()}</p>
              </div>
              <Wallet className="w-8 h-8 text-blue-400" />
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">BTC Price</p>
                <p className="text-2xl font-bold">${currentPrice.price}</p>
                <p className="text-green-400 text-sm">{currentPrice.change}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Active Trades</p>
                <p className="text-2xl font-bold">{tradeHistory.length}</p>
              </div>
              <Activity className="w-8 h-8 text-orange-400" />
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">24h PnL</p>
                <p className="text-2xl font-bold text-green-400">+$234.56</p>
              </div>
              <DollarSign className="w-8 h-8 text-green-400" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Chart and Trading */}
          <div className="lg:col-span-2 space-y-6">
            {/* Price Chart */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Price Chart</h2>
                <select 
                  value={selectedSymbol} 
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                  className="bg-gray-700 text-white px-3 py-2 rounded"
                >
                  <option value="BTCUSDT">BTC/USDT</option>
                  <option value="ETHUSDT">ETH/USDT</option>
                  <option value="BNBUSDT">BNB/USDT</option>
                </select>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={priceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                    labelStyle={{ color: '#9CA3AF' }}
                  />
                  <Line type="monotone" dataKey="price" stroke="#10B981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Trading Form */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Place Order</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Symbol</label>
                  <select 
                    value={tradeForm.symbol} 
                    onChange={(e) => setTradeForm({...tradeForm, symbol: e.target.value})}
                    className="w-full bg-gray-700 text-white px-3 py-2 rounded"
                  >
                    <option value="BTCUSDT">BTC/USDT</option>
                    <option value="ETHUSDT">ETH/USDT</option>
                    <option value="BNBUSDT">BNB/USDT</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Side</label>
                  <select 
                    value={tradeForm.side} 
                    onChange={(e) => setTradeForm({...tradeForm, side: e.target.value})}
                    className="w-full bg-gray-700 text-white px-3 py-2 rounded"
                  >
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Order Type</label>
                  <select 
                    value={tradeForm.type} 
                    onChange={(e) => setTradeForm({...tradeForm, type: e.target.value})}
                    className="w-full bg-gray-700 text-white px-3 py-2 rounded"
                  >
                    <option value="MARKET">MARKET</option>
                    <option value="LIMIT">LIMIT</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Quantity</label>
                  <input
                    type="number"
                    step="0.00001"
                    value={tradeForm.quantity}
                    onChange={(e) => setTradeForm({...tradeForm, quantity: e.target.value})}
                    className="w-full bg-gray-700 text-white px-3 py-2 rounded"
                    placeholder="0.001"
                  />
                </div>
                
                {tradeForm.type === 'LIMIT' && (
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium mb-2">Price</label>
                    <input
                      type="number"
                      step="0.01"
                      value={tradeForm.price}
                      onChange={(e) => setTradeForm({...tradeForm, price: e.target.value})}
                      className="w-full bg-gray-700 text-white px-3 py-2 rounded"
                      placeholder="41500"
                    />
                  </div>
                )}
              </div>
              
              <button
                onClick={executeTrade}
                disabled={loading}
                className={`w-full mt-4 py-3 rounded font-medium transition-colors ${
                  tradeForm.side === 'BUY' 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-red-600 hover:bg-red-700'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? 'Executing...' : `${tradeForm.side} ${tradeForm.symbol}`}
              </button>
            </div>
          </div>

          {/* Right Column - Balances and History */}
          <div className="space-y-6">
            {/* Wallet Balances */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Wallet Balances</h2>
              <div className="space-y-3">
                {balances.map((balance, index) => (
                  <div key={index} className="flex justify-between items-center py-2 border-b border-gray-700">
                    <div>
                      <p className="font-medium">{balance.asset}</p>
                      <p className="text-sm text-gray-400">{balance.free}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">${balance.usdValue.toLocaleString()}</p>
                      <p className="text-sm text-gray-400">Available</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trade History */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Recent Trades</h2>
              <div className="space-y-3">
                {tradeHistory.map((trade) => (
                  <div key={trade.id} className="flex justify-between items-center py-2 border-b border-gray-700">
                    <div>
                      <p className="font-medium">{trade.symbol}</p>
                      <p className="text-sm text-gray-400">{trade.time}</p>
                    </div>
                    <div className="text-right">
                      <p className={`font-medium ${trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.side} {trade.quantity}
                      </p>
                      <p className="text-sm text-gray-400">${trade.price}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;