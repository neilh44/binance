# security.py - Security utilities and middleware
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import hashlib
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Security management for the trading API"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # Redis for rate limiting (optional)
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        except:
            self.redis_client = None
            logger.warning("Redis not available, rate limiting disabled")
    
    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def rate_limit_check(self, key: str, limit: int = 100, window: int = 3600) -> bool:
        """Check rate limit for a key"""
        if not self.redis_client:
            return True
        
        try:
            current = self.redis_client.get(key)
            if current is None:
                self.redis_client.setex(key, window, 1)
                return True
            
            if int(current) >= limit:
                return False
            
            self.redis_client.incr(key)
            return True
        except:
            return True  # Allow request if Redis fails
    
    def validate_api_signature(self, api_key: str, signature: str, timestamp: str, body: str) -> bool:
        """Validate API signature for additional security"""
        expected_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            f"{timestamp}{body}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

# Authentication dependencies
security = HTTPBearer()
security_manager = SecurityManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials
    return security_manager.verify_token(token)

# monitoring.py - Monitoring and logging utilities
import time
import psutil
from datetime import datetime
from typing import Dict, List
import asyncio
from contextlib import asynccontextmanager

class MonitoringManager:
    """System monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_by_endpoint': {},
            'response_times': {},
            'errors_total': 0,
            'active_connections': 0,
            'trades_executed': 0,
            'api_calls_made': 0
        }
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Record API request metrics"""
        self.metrics['requests_total'] += 1
        
        key = f"{method}:{endpoint}"
        if key not in self.metrics['requests_by_endpoint']:
            self.metrics['requests_by_endpoint'][key] = 0
        self.metrics['requests_by_endpoint'][key] += 1
        
        if key not in self.metrics['response_times']:
            self.metrics['response_times'][key] = []
        self.metrics['response_times'][key].append(response_time)
        
        if status_code >= 400:
            self.metrics['errors_total'] += 1
    
    def record_trade(self):
        """Record trade execution"""
        self.metrics['trades_executed'] += 1
    
    def record_api_call(self):
        """Record Binance API call"""
        self.metrics['api_calls_made'] += 1
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        return {
            'uptime': time.time() - self.start_time,
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict()
        }
    
    def get_api_metrics(self) -> Dict:
        """Get API performance metrics"""
        avg_response_times = {}
        for endpoint, times in self.metrics['response_times'].items():
            avg_response_times[endpoint] = sum(times) / len(times) if times else 0
        
        return {
            'requests_total': self.metrics['requests_total'],
            'requests_by_endpoint': self.metrics['requests_by_endpoint'],
            'average_response_times': avg_response_times,
            'errors_total': self.metrics['errors_total'],
            'error_rate': (self.metrics['errors_total'] / max(1, self.metrics['requests_total'])) * 100,
            'trades_executed': self.metrics['trades_executed'],
            'api_calls_made': self.metrics['api_calls_made']
        }
    
    def get_health_status(self) -> Dict:
        """Get application health status"""
        system_metrics = self.get_system_metrics()
        api_metrics = self.get_api_metrics()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if system_metrics['cpu_usage'] > 80:
            health_status = "warning"
            issues.append("High CPU usage")
        
        if system_metrics['memory_usage'] > 85:
            health_status = "warning"
            issues.append("High memory usage")
        
        if api_metrics['error_rate'] > 10:
            health_status = "unhealthy"
            issues.append("High error rate")
        
        return {
            'status': health_status,
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'system_metrics': system_metrics,
            'api_metrics': api_metrics
        }

# Middleware for monitoring
monitor = MonitoringManager()

@asynccontextmanager
async def monitoring_middleware(request, call_next):
    """Middleware to monitor requests"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        monitor.record_request(
            endpoint=request.url.path,
            method=request.method,
            response_time=process_time,
            status_code=response.status_code
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        monitor.record_request(
            endpoint=request.url.path,
            method=request.method,
            response_time=process_time,
            status_code=500
        )
        raise

# Add these endpoints to your main FastAPI app
@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return monitor.get_health_status()

@app.get("/api/metrics")
async def get_metrics():
    """Get application metrics"""
    return {
        'system': monitor.get_system_metrics(),
        'api': monitor.get_api_metrics(),
        'timestamp': datetime.now().isoformat()
    }

# Enhanced error handling
class TradingAPIException(Exception):
    """Custom exception for trading API"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

@app.exception_handler(TradingAPIException)
async def trading_exception_handler(request, exc: TradingAPIException):
    """Handle custom trading exceptions"""
    logger.error(f"Trading API error: {exc.message}", extra={'details': exc.details})
    
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "timestamp": datetime.now().isoformat()
        }
    )

# Configuration management
class Config:
    """Application configuration"""
    
    def __init__(self):
        self.binance_api_key = os.getenv("BINANCE_API_KEY")
        self.binance_secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "default-secret")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_trade_amount = float(os.getenv("MAX_TRADE_AMOUNT", "1000"))
        self.enable_testnet = os.getenv("ENABLE_TESTNET", "true").lower() == "true"
    
    def validate(self):
        """Validate configuration"""
        if not self.binance_api_key or not self.binance_secret_key:
            raise ValueError("Binance API credentials are required")
        
        if len(self.jwt_secret_key) < 32:
            logger.warning("JWT secret key should be at least 32 characters long")
    
    def get_binance_client_config(self):
        """Get Binance client configuration"""
        return {
            'api_key': self.binance_api_key,
            'api_secret': self.binance_secret_key,
            'testnet': self.enable_testnet
        }

# Logging configuration
def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=getattr(logging, Config().log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_api.log'),
            logging.StreamHandler()
        ]
    )
    
    # Set up structured logging for important events
    trading_logger = logging.getLogger('trading')
    trading_logger.setLevel(logging.INFO)
    
    return trading_logger

# Initialize configuration and logging
config = Config()
config.validate()
trading_logger = setup_logging()