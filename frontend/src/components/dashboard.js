import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Wallet, Activity, AlertCircle, RefreshCw, X } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const BinanceTradingDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [marketData, setMarketData] = useState([]);
  const [balance, setBalance] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [symbolData, setSymbolData] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [openOrders, setOpenOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tradeForm, setTradeForm] = useState({
    symbol: 'BTCUSDT',
    side: 'BUY',
    type: 'MARKET',
    quantity: '',
    price: ''
  });

  const fetchMarketData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/market-overview`);
      const data = await response.json();
      setMarketData(data);
    } catch (err) {
      setError('Failed to fetch market data');
    }
  };

  const fetchBalance = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/balance`);
      const data = await response.json();
      setBalance(data);
    } catch (err) {
      setError('Failed to fetch balance');
    }
  };

  const fetchSymbolData = async (symbol) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/market/${symbol}`);
      const data = await response.json();
      setSymbolData(data);
    } catch (err) {
      setError('Failed to fetch symbol data');
    }
  };

  const fetchTradeHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history`);
      const data = await response.json();
      setTradeHistory(data);
    } catch (err) {
      setError('Failed to fetch trade history');
    }
  };

  const fetchOpenOrders = async (symbol) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/orders/${symbol}`);
      const data = await response.json();
      setOpenOrders(data);
    } catch (err) {
      setError('Failed to fetch open orders');
    }
  };

  const executeTrade = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tradeForm)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Trade execution failed');
      }
      
      const result = await response.json();
      alert(`Trade executed successfully! Order ID: ${result.orderId}`);
      setTradeForm({ ...tradeForm, quantity: '', price: '' });
      fetchBalance();
      fetchTradeHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const cancelOrder = async (orderId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/orders/${selectedSymbol}/${orderId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to cancel order');
      }
      
      alert('Order cancelled successfully');
      fetchOpenOrders(selectedSymbol);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchMarketData();
    fetchBalance();
    fetchTradeHistory();
    const interval = setInterval(() => {
      fetchMarketData();
      fetchBalance();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      fetchSymbolData(selectedSymbol);
      fetchOpenOrders(selectedSymbol);
    }
  }, [selectedSymbol]);

  const ErrorAlert = ({ message, onClose }) => (
    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
      <div className="flex items-center">
        <AlertCircle className="w-5 h-5 mr-2" />
        <span>{message}</span>
        <button onClick={onClose} className="ml-auto">
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );

  const MarketOverview = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Market Overview</h2>
        <button
          onClick={fetchMarketData}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {marketData.map((market) => (
          <div
            key={market.symbol}
            className="bg-white p-4 rounded-lg shadow cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => setSelectedSymbol(market.symbol)}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg">{market.symbol}</h3>
              <div className={`flex items-center ${
                market.change.includes('+') ? 'text-green-500' : 'text-red-500'
              }`}>
                {market.change.includes('+') ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                <span className="ml-1">{market.change}</span>
              </div>
            </div>
            <p className="text-2xl font-bold">${market.price}</p>
            <div className="mt-2 text-sm text-gray-600">
              <p>Volume: {market.volume}</p>
              <p>High: ${market.high} | Low: ${market.low}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const Portfolio = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Portfolio</h2>
        <button
          onClick={fetchBalance}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {balance.map((asset) => (
          <div key={asset.asset} className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg">{asset.asset}</h3>
              <Wallet className="w-5 h-5 text-gray-500" />
            </div>
            <p className="text-xl font-bold">{parseFloat(asset.free).toFixed(6)}</p>
            <p className="text-sm text-gray-600">Locked: {parseFloat(asset.locked).toFixed(6)}</p>
            <p className="text-sm text-green-600">≈ ${asset.usdValue}</p>
          </div>
        ))}
      </div>
    </div>
  );

  const Trading = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Trading</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold mb-4">{selectedSymbol} Chart</h3>
          {symbolData?.chartData && (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={symbolData.chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
        
        {/* Trading Form */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold mb-4">Place Order</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Symbol</label>
              <select
                value={tradeForm.symbol}
                onChange={(e) => setTradeForm({ ...tradeForm, symbol: e.target.value })}
                className="w-full p-2 border rounded"
              >
                {marketData.map((market) => (
                  <option key={market.symbol} value={market.symbol}>
                    {market.symbol}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Side</label>
                <select
                  value={tradeForm.side}
                  onChange={(e) => setTradeForm({ ...tradeForm, side: e.target.value })}
                  className="w-full p-2 border rounded"
                >
                  <option value="BUY">Buy</option>
                  <option value="SELL">Sell</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Type</label>
                <select
                  value={tradeForm.type}
                  onChange={(e) => setTradeForm({ ...tradeForm, type: e.target.value })}
                  className="w-full p-2 border rounded"
                >
                  <option value="MARKET">Market</option>
                  <option value="LIMIT">Limit</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Quantity</label>
              <input
                type="number"
                value={tradeForm.quantity}
                onChange={(e) => setTradeForm({ ...tradeForm, quantity: e.target.value })}
                className="w-full p-2 border rounded"
                placeholder="Enter quantity"
              />
            </div>
            
            {tradeForm.type === 'LIMIT' && (
              <div>
                <label className="block text-sm font-medium mb-2">Price</label>
                <input
                  type="number"
                  value={tradeForm.price}
                  onChange={(e) => setTradeForm({ ...tradeForm, price: e.target.value })}
                  className="w-full p-2 border rounded"
                  placeholder="Enter price"
                />
              </div>
            )}
            
            <button
              onClick={executeTrade}
              disabled={loading || !tradeForm.quantity}
              className="w-full py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
            >
              {loading ? 'Executing...' : `${tradeForm.side} ${tradeForm.symbol}`}
            </button>
          </div>
        </div>
      </div>
      
      {/* Open Orders */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="font-semibold mb-4">Open Orders for {selectedSymbol}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Order ID</th>
                <th className="text-left p-2">Side</th>
                <th className="text-left p-2">Type</th>
                <th className="text-left p-2">Quantity</th>
                <th className="text-left p-2">Price</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {openOrders.map((order) => (
                <tr key={order.orderId} className="border-b">
                  <td className="p-2">{order.orderId}</td>
                  <td className="p-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      order.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {order.side}
                    </span>
                  </td>
                  <td className="p-2">{order.type}</td>
                  <td className="p-2">{order.quantity}</td>
                  <td className="p-2">{order.price}</td>
                  <td className="p-2">{order.status}</td>
                  <td className="p-2">
                    <button
                      onClick={() => cancelOrder(order.orderId)}
                      className="text-red-500 hover:text-red-700"
                    >
                      Cancel
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {openOrders.length === 0 && (
            <p className="text-gray-500 text-center py-4">No open orders</p>
          )}
        </div>
      </div>
    </div>
  );

  const History = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Trade History</h2>
        <button
          onClick={fetchTradeHistory}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
      
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3">Symbol</th>
                <th className="text-left p-3">Side</th>
                <th className="text-left p-3">Quantity</th>
                <th className="text-left p-3">Price</th>
                <th className="text-left p-3">Time</th>
                <th className="text-left p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {tradeHistory.map((trade) => (
                <tr key={trade.id} className="border-b">
                  <td className="p-3 font-medium">{trade.symbol}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {trade.side}
                    </span>
                  </td>
                  <td className="p-3">{trade.quantity}</td>
                  <td className="p-3">${trade.price}</td>
                  <td className="p-3">{trade.time}</td>
                  <td className="p-3">
                    <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                      {trade.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {tradeHistory.length === 0 && (
            <p className="text-gray-500 text-center py-8">No trade history</p>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-3xl font-bold text-gray-900">Binance Trading Dashboard</h1>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Total Balance: ${balance.reduce((sum, asset) => sum + asset.usdValue, 0).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'overview', label: 'Market Overview', icon: TrendingUp },
              { id: 'portfolio', label: 'Portfolio', icon: Wallet },
              { id: 'trading', label: 'Trading', icon: Activity },
              { id: 'history', label: 'History', icon: Activity }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
        
        {activeTab === 'overview' && <MarketOverview />}
        {activeTab === 'portfolio' && <Portfolio />}
        {activeTab === 'trading' && <Trading />}
        {activeTab === 'history' && <History />}
      </main>
    </div>
  );
};

export default BinanceTradingDashboard;