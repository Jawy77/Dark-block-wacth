# backend/models/schemas.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

class WalletBase(BaseModel):
    address: str = Field(..., description="Ethereum wallet address")

class WalletInfo(WalletBase):
    balance: float = Field(0.0, description="Current ETH balance")
    transaction_count: int = Field(0, description="Total number of transactions")
    first_transaction: Optional[datetime] = Field(None, description="Timestamp of first transaction")
    last_transaction: Optional[datetime] = Field(None, description="Timestamp of last transaction")
    token_count: int = Field(0, description="Number of different tokens held")

class Transaction(BaseModel):
    hash: str = Field(..., description="Transaction hash")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Recipient address")
    value: float = Field(..., description="Transaction value in ETH")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    gas_price: float = Field(..., description="Gas price in Gwei")
    status: bool = Field(..., description="Transaction status (success/failure)")

class TokenInfo(BaseModel):
    address: str = Field(..., description="Token contract address")
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")
    decimals: int = Field(..., description="Token decimals")
    balance: float = Field(..., description="Token balance")
    price_usd: Optional[float] = Field(None, description="Current price in USD")

class RiskFactor(BaseModel):
    name: str = Field(..., description="Name of the risk factor")
    description: str = Field(..., description="Description of the risk factor")
    severity: str = Field(..., description="Risk severity (LOW, MEDIUM, HIGH)")
    score_contribution: float = Field(..., ge=0, le=100, description="Contribution to risk score")

class RiskAnalysis(BaseModel):
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score")
    risk_level: str = Field(..., pattern="^(LOW|MEDIUM|HIGH)$", description="Risk level category")
    risk_factors: List[RiskFactor] = Field(default=[], description="Identified risk factors")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

class WalletAnalysis(BaseModel):
    wallet_info: WalletInfo
    risk_analysis: RiskAnalysis
    recent_transactions: List[Transaction] = Field(default=[], description="Recent transactions")
    tokens: List[TokenInfo] = Field(default=[], description="Token holdings")
    connected_addresses: List[str] = Field(default=[], description="Connected wallet addresses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "wallet_info": {
                    "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                    "balance": 1.5,
                    "transaction_count": 100,
                    "first_transaction": "2024-01-01T00:00:00Z",
                    "last_transaction": "2024-02-15T12:30:00Z",
                    "token_count": 5
                },
                "risk_analysis": {
                    "risk_score": 75.5,
                    "risk_level": "HIGH",
                    "risk_factors": [
                        {
                            "name": "High Value Transactions",
                            "description": "Multiple high-value transactions detected",
                            "severity": "HIGH",
                            "score_contribution": 30.0
                        }
                    ],
                    "analysis_timestamp": "2024-02-15T12:30:00Z"
                }
            }
        }

# Schemas para autenticación
class SignatureRequest(BaseModel):
    address: str = Field(..., description="Wallet address")
    message: str = Field(..., description="Message to sign")
    signature: str = Field(..., description="Signed message")

class AuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

# Schemas para respuestas API
class APIResponse(BaseModel):
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class ErrorResponse(BaseModel):
    status: str = Field(default="error", description="Error status")
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
