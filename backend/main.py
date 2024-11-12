# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import Optional
import asyncio

# Importar servicios
from services.blockchain_service import BlockchainService
from services.ml_service import MLService

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="DarkBlock Watch API",
    description="Blockchain wallet analysis and fraud detection API",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGINS", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servicios
blockchain_service = None
ml_service = None

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar la aplicación"""
    global blockchain_service, ml_service
    blockchain_service = BlockchainService()
    ml_service = MLService()

@app.get("/")
async def read_root():
    return {
        "name": "DarkBlock Watch API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {
            "ethplorer": bool(os.getenv("ETHPLORER_API_KEY")),
            "infura": bool(os.getenv("INFURA_API_KEY"))
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Rutas para el análisis de wallets
@app.get("/wallet/{address}")
async def get_wallet_info(address: str):
    try:
        if not blockchain_service:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        wallet_data = await blockchain_service.analyze_wallet(address)
        return {
            "status": "success",
            "data": wallet_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transactions/{address}")
async def get_transactions(address: str, limit: Optional[int] = 100):
    try:
        if not blockchain_service:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        transactions = await blockchain_service.get_transactions(address, limit)
        return {
            "status": "success",
            "data": transactions,
            "count": len(transactions),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tokens/{address}")
async def get_tokens(address: str):
    try:
        if not blockchain_service:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        tokens = await blockchain_service.get_token_holdings(address)
        return {
            "status": "success",
            "data": tokens,
            "count": len(tokens),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk-score/{address}")
async def get_risk_score(address: str):
    try:
        if not blockchain_service or not ml_service:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Obtener datos de la wallet
        wallet_data = await blockchain_service.analyze_wallet(address)
        
        # Realizar análisis de riesgo
        risk_analysis = await ml_service.analyze_wallet(wallet_data)
        
        return {
            "status": "success",
            "address": address,
            "risk_analysis": risk_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
