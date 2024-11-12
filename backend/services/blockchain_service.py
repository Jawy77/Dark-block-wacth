# services/blockchain_service.py
import aiohttp
import asyncio
from web3 import Web3
import os
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

class BlockchainService:
    def __init__(self):
        load_dotenv()
        self.ethplorer_key = os.getenv("ETHPLORER_API_KEY")
        self.infura_id = os.getenv("INFURA_API_KEY")
        self.ethplorer_url = "https://api.ethplorer.io"
        
        # Inicializar Web3
        self.w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{self.infura_id}"))

    async def get_token_holdings(self, address: str) -> List[Dict]:
        """Obtener los tokens de una wallet"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ethplorer_url}/getAddressInfo/{address}"
                params = {
                    "apiKey": self.ethplorer_key,
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Verificar que data sea un diccionario y tenga la clave 'tokens'
                        if isinstance(data, dict) and 'tokens' in data:
                            return self._process_token_holdings(data['tokens'])
                        return []  # Retornar lista vacía si no hay tokens
                    raise Exception(f"API Error: {response.status}")
        except Exception as e:
            raise Exception(f"Error fetching token holdings: {str(e)}")

    def _process_token_holdings(self, tokens: List) -> List[Dict]:
        """Procesa la información de tokens"""
        processed_tokens = []
        
        # Verificar que tokens sea una lista
        if not isinstance(tokens, list):
            return processed_tokens
            
        for token in tokens:
            # Verificar que token sea un diccionario
            if not isinstance(token, dict):
                continue
                
            token_info = token.get('tokenInfo', {})
            # Verificar que token_info sea un diccionario
            if not isinstance(token_info, dict):
                continue
                
            try:
                decimals = int(token_info.get('decimals', 18))
                balance = float(token.get('balance', 0))
                
                # Procesar precio
                price_info = token_info.get('price', {})
                price_usd = float(price_info.get('rate', 0)) if isinstance(price_info, dict) else 0
                
                processed_tokens.append({
                    "name": token_info.get('name', 'Unknown'),
                    "symbol": token_info.get('symbol', 'Unknown'),
                    "address": token_info.get('address', ''),
                    "balance": balance / (10 ** decimals),
                    "decimals": decimals,
                    "price_usd": price_usd,
                    "total_value_usd": (balance / (10 ** decimals)) * price_usd
                })
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Error processing token: {str(e)}")
                continue
                
        return processed_tokens

    async def get_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """Obtener transacciones de una wallet"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ethplorer_url}/getAddressTransactions/{address}"
                params = {
                    "apiKey": self.ethplorer_key,
                    "limit": limit
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        transactions = await response.json()
                        if isinstance(transactions, list):
                            return self._process_transactions(transactions)
                        return []
                    raise Exception(f"API Error: {response.status}")
        except Exception as e:
            raise Exception(f"Error fetching transactions: {str(e)}")

    def _process_transactions(self, transactions: List) -> List[Dict]:
        """Procesa las transacciones"""
        processed_txs = []
        
        for tx in transactions:
            if not isinstance(tx, dict):
                continue
                
            try:
                processed_txs.append({
                    "hash": tx.get("hash", ""),
                    "from": tx.get("from", ""),
                    "to": tx.get("to", ""),
                    "value": float(tx.get("value", 0)),
                    "timestamp": datetime.fromtimestamp(int(tx.get("timestamp", 0))).isoformat(),
                    "gas_price": float(tx.get("gasPrice", 0)),
                    "success": bool(tx.get("success", True))
                })
            except (ValueError, TypeError) as e:
                print(f"Error processing transaction: {str(e)}")
                continue
                
        return processed_txs

    async def analyze_wallet(self, address: str) -> Dict:
        """Análisis completo de una wallet"""
        try:
            # Verificar formato de dirección
            if not self.w3.is_address(address):
                raise ValueError("Invalid Ethereum address format")
            
            # Ejecutar consultas en paralelo
            transactions, tokens = await asyncio.gather(
                self.get_transactions(address),
                self.get_token_holdings(address)
            )
            
            # Calcular estadísticas básicas
            total_value = sum(token.get('total_value_usd', 0) for token in tokens)
            total_tx_value = sum(tx.get('value', 0) for tx in transactions)
            
            return {
                "address": address,
                "transactions": transactions,
                "token_holdings": tokens,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "stats": {
                    "total_transactions": len(transactions),
                    "total_tokens": len(tokens),
                    "total_token_value_usd": total_value,
                    "total_eth_value": total_tx_value
                }
            }
        except ValueError as ve:
            raise Exception(f"Validation error: {str(ve)}")
        except Exception as e:
            raise Exception(f"Wallet analysis failed: {str(e)}")

    async def get_eth_balance(self, address: str) -> float:
        """Obtener balance de ETH"""
        try:
            balance_wei = self.w3.eth.get_balance(address)
            return float(self.w3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            raise Exception(f"Error fetching ETH balance: {str(e)}")
