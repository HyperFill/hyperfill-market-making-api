from orderbook import OrderBook
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import uvicorn
from decimal import Decimal
import time
import os
from typing import Optional

from dotenv import load_dotenv

# import asyncio
import logging
from web3 import Web3

# Import the TradeSettlementClient
from orderbook.trade_settlement_client import TradeSettlementClient, AllowanceChecker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

order_books = {}  # Dictionary to store multiple order books, keyed by symbol
app = FastAPI()

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global settlement client - initialize on startup
settlement_client: Optional[TradeSettlementClient] = None
allowance_checker: Optional[AllowanceChecker] = None

# Configuration - you should move these to environment variables
WEB3_PROVIDER = os.getenv("WEB3_PROVIDER", "https://your-ethereum-node.com")
CONTRACT_ADDRESS = os.getenv(
    "CONTRACT_ADDRESS", "0xF14dbF48b727AD8346dD8Fa6C0FC42FCb81FF115"
)
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # Should be loaded securely
CONTRACT_ABI = []  # Load your contract ABI here

# Token address mapping - you should expand this
TOKEN_ADDRESSES = {
    "SEI": os.getenv("SEI_TOKEN_ADDRESS", "0x8eFcF5c2DDDA6C1A63D8395965Ca6c0609CE32D5"),
    "USDT": os.getenv(
        "USDT_TOKEN_ADDRESS", "0x54099052D0e04a5CF24e4c7c82eA693Fb25E0Bed"
    ),
}


@app.on_event("startup")
async def startup_event():
    """Initialize settlement client on startup"""
    global settlement_client, allowance_checker

    CONTRACT_ABI = load_abi("orderbook/settlement_abi.json")
    # print(CONTRACT_ABI)

    try:
        settlement_client = TradeSettlementClient(
            WEB3_PROVIDER,
            CONTRACT_ADDRESS,
            CONTRACT_ABI,
            PRIVATE_KEY,
        )
        allowance_checker = AllowanceChecker(WEB3_PROVIDER)
        logger.info("Settlement client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize settlement client: {e}")
        # You might want to exit here if settlement is critical


def get_token_address(symbol: str) -> str:
    """Get token address from symbol"""
    token_address = TOKEN_ADDRESSES.get(symbol.upper(), symbol)
    print(token_address, "TOKEN_ADDRESS")
    return token_address


def load_abi(abi_path):
    """Load ABI from relative path and return it"""
    with open(abi_path, "r") as f:
        data = json.load(f)
    return data["abi"] if isinstance(data, dict) and "abi" in data else data


async def validate_order_prerequisites(order_data: dict) -> dict:
    """Validate that user has sufficient balance and allowance for the order"""
    if not settlement_client:
        return {"valid": False, "error": "Settlement client not available"}

    try:
        account = order_data["account"]
        base_asset = order_data["baseAsset"]
        quote_asset = order_data["quoteAsset"]
        price = Decimal(str(order_data["price"]))
        quantity = Decimal(str(order_data["quantity"]))
        side = order_data["side"]

        base_token_addr = get_token_address(base_asset)
        quote_token_addr = get_token_address(quote_asset)

        # Convert amounts to proper units (assuming 18 decimals)
        base_amount = int(quantity * (10**18))
        quote_amount = int(quantity * price * (10**18))

        validation_result = {"valid": True, "errors": [], "warnings": [], "checks": {}}

        if side.lower() == "bid":
            # Bidder needs quote asset (e.g., USDT) allowance and balance
            allowance_sufficient, current_allowance = settlement_client.check_allowance(
                account, quote_token_addr, quote_amount
            )
            balance_sufficient, current_balance = settlement_client.check_balance(
                account, quote_token_addr, quote_amount
            )

            validation_result["checks"] = {
                "required_asset": quote_asset,
                "required_amount": float(quantity * price),
                "current_allowance": current_allowance / (10**18),
                "current_balance": current_balance / (10**18),
                "allowance_sufficient": allowance_sufficient,
                "balance_sufficient": balance_sufficient,
            }

            if not allowance_sufficient:
                validation_result["errors"].append(
                    f"Insufficient {quote_asset} allowance. Required: {float(quantity * price)}, Current: {current_allowance / (10 ** 18)}"
                )
                validation_result["valid"] = False

            if not balance_sufficient:
                validation_result["errors"].append(
                    f"Insufficient {quote_asset} balance. Required: {float(quantity * price)}, Current: {current_balance / (10 ** 18)}"
                )
                validation_result["valid"] = False

        elif side.lower() == "ask":
            # Asker needs base asset (e.g., SEI) allowance and balance
            allowance_sufficient, current_allowance = settlement_client.check_allowance(
                account, base_token_addr, base_amount
            )
            balance_sufficient, current_balance = settlement_client.check_balance(
                account, base_token_addr, base_amount
            )

            validation_result["checks"] = {
                "required_asset": base_asset,
                "required_amount": float(quantity),
                "current_allowance": current_allowance / (10**18),
                "current_balance": current_balance / (10**18),
                "allowance_sufficient": allowance_sufficient,
                "balance_sufficient": balance_sufficient,
            }

            if not allowance_sufficient:
                validation_result["errors"].append(
                    f"Insufficient {base_asset} allowance. Required: {float(quantity)}, Current: {current_allowance / (10 ** 18)}"
                )
                validation_result["valid"] = False

            if not balance_sufficient:
                validation_result["errors"].append(
                    f"Insufficient {base_asset} balance. Required: {float(quantity)}, Current: {current_balance / (10 ** 18)}"
                )
                validation_result["valid"] = False

        return validation_result

    except Exception as e:
        logger.error(f"Error validating order prerequisites: {e}")
        return {"valid": False, "error": str(e)}


def create_trade_signature_for_user(
    party_addr: str,
    order_id: int,
    base_asset: str,
    quote_asset: str,
    price: int,
    quantity: int,
    side: str,
    timestamp: int,
    nonce: int,
) -> str:
    """Create a signature for a party (in production, this would be done client-side)"""
    try:
        # This is a simplified version - in production, each party would sign their own order
        # You'll need to implement proper signature generation or have users sign on the frontend

        # For now, return a placeholder signature that indicates signature is needed
        # The actual signature would be created using the party's private key]
        return settlement_client.create_trade_signature(
            party_addr,
            order_id,
            base_asset,
            quote_asset,
            price,
            quantity,
            side,
            timestamp,
            nonce,
        )
        # return "0x" + "0" * 130  # Placeholder - replace with actual signature logic

    except Exception as e:
        logger.error(f"Error creating signature: {e}")
        return ""


async def settle_trades_if_any(order_dict: dict) -> dict:
    """Settle trades if any exist in the order response"""
    if not settlement_client or not order_dict.get("trades"):
        return {"settled": False, "reason": "No trades to settle or client unavailable"}

    settlement_results = []

    try:
        for trade in order_dict["trades"]:
            # Extract trade parties information
            party1_addr = trade["party1"][0]
            party1_priv_key = trade["party1"][4]
            party1_side = trade["party1"][1]
            party1_order_id = trade["party1"][2]
            party1_remaining_qty = trade["party1"][3]

            party2_addr = trade["party2"][0]
            party2_side = trade["party2"][1]
            party2_priv_key = trade["party2"][4]

            party2_order_id = trade["party2"][2]
            party2_remaining_qty = trade["party2"][3]

            # Get token addresses
            base_token_addr = get_token_address(order_dict["baseAsset"])
            quote_token_addr = get_token_address(order_dict["quoteAsset"])

            # Get nonces for both parties using base asset
            nonce1 = settlement_client.get_user_nonce(party1_addr, base_token_addr)
            nonce2 = settlement_client.get_user_nonce(party2_addr, base_token_addr)

            # Convert amounts to proper units (18 decimals)
            price_wei = int(float(trade["price"]) * (10**18))
            quantity_wei = int(float(trade["quantity"]) * (10**18))

            # Create TradeExecution struct data
            trade_execution = {
                "orderId": order_dict["orderId"],
                "account": order_dict["account"],
                "price": price_wei,
                "quantity": quantity_wei,
                "side": order_dict["side"],
                "baseAsset": base_token_addr,
                "quoteAsset": quote_token_addr,
                "tradeId": str(order_dict["trade_id"]),
                "timestamp": trade["timestamp"],
                "isValid": order_dict["isValid"],
            }

            # For the quantities passed to settleTrade function:
            # These represent the quantities each party is trading
            party1_quantity = quantity_wei  # Both parties trade the same base quantity
            party2_quantity = quantity_wei

            # Create signatures for both parties
            # NOTE: In production, these signatures should be created by the actual users
            # Either on the frontend or through a secure signing service
            signature1 = create_trade_signature_for_user(
                party1_priv_key,
                trade_execution["orderId"],
                base_token_addr,
                quote_token_addr,
                price_wei,
                party1_quantity,
                party1_side,
                trade["timestamp"],
                nonce1,
            )

            signature2 = create_trade_signature_for_user(
                party2_priv_key,
                trade_execution["orderId"],
                base_token_addr,
                quote_token_addr,
                price_wei,
                party2_quantity,
                party2_side,
                trade["timestamp"],
                nonce2,
            )

            # Attempt settlement
            logger.info(f"Attempting to settle trade: {trade}")

            try:
                # Build the settlement transaction
                settlement_function = settlement_client.contract.functions.settleTrade(
                    (
                        trade_execution["orderId"],
                        Web3.to_checksum_address(trade_execution["account"]),
                        trade_execution["price"],
                        trade_execution["quantity"],
                        trade_execution["side"],
                        Web3.to_checksum_address(trade_execution["baseAsset"]),
                        Web3.to_checksum_address(trade_execution["quoteAsset"]),
                        trade_execution["tradeId"],
                        trade_execution["timestamp"],
                        trade_execution["isValid"],
                    ),
                    Web3.to_checksum_address(party1_addr),
                    Web3.to_checksum_address(party2_addr),
                    party1_quantity,
                    party2_quantity,
                    party1_side,
                    party2_side,
                    bytes.fromhex(signature1.replace("0x", "")),
                    bytes.fromhex(signature2.replace("0x", "")),
                    nonce1,
                    nonce2,
                )

                # Check if we have a private key for transaction signing
                if not settlement_client.account:
                    settlement_result = {
                        "success": False,
                        "error": "No private key available for transaction signing",
                        "trade_data": trade_execution,
                    }
                else:
                    # Estimate gas
                    try:
                        gas_estimate = settlement_function.estimate_gas(
                            {"from": settlement_client.account.address}
                        )
                    except Exception as gas_error:
                        logger.error(f"Gas estimation failed: {gas_error}")
                        settlement_result = {
                            "success": False,
                            "error": f"Gas estimation failed: {str(gas_error)}",
                            "trade_data": trade_execution,
                        }
                        settlement_results.append(
                            {"trade": trade, "settlement_result": settlement_result}
                        )
                        continue

                    # Build transaction
                    transaction = settlement_function.build_transaction(
                        {
                            "from": settlement_client.account.address,
                            "gas": int(gas_estimate * 1.2),  # Add 20% buffer
                            "gasPrice": settlement_client.web3.to_wei("20", "gwei"),
                            "nonce": settlement_client.web3.eth.get_transaction_count(
                                settlement_client.account.address
                            ),
                        }
                    )

                    # Sign and send transaction
                    signed_txn = settlement_client.web3.eth.account.sign_transaction(
                        transaction, settlement_client.account.key
                    )
                    tx_hash = settlement_client.web3.eth.send_raw_transaction(
                        signed_txn.raw_transaction
                    )

                    # Wait for receipt
                    receipt = settlement_client.web3.eth.wait_for_transaction_receipt(
                        tx_hash, timeout=120
                    )

                    settlement_result = {
                        "success": receipt.status == 1,
                        "transaction_hash": receipt.transactionHash.hex(),
                        "gas_used": receipt.gasUsed,
                        "block_number": receipt.blockNumber,
                        "trade_data": trade_execution,
                    }

            except Exception as settle_error:
                logger.error(f"Settlement error: {settle_error}")
                settlement_result = {
                    "success": False,
                    "error": str(settle_error),
                    "trade_data": trade_execution,
                }

            settlement_results.append(
                {"trade": trade, "settlement_result": settlement_result}
            )

            if settlement_result["success"]:
                logger.info(
                    f"Trade settled successfully: {settlement_result.get('transaction_hash', 'N/A')}"
                )
            else:
                logger.error(
                    f"Trade settlement failed: {settlement_result.get('error', 'Unknown error')}"
                )

    except Exception as e:
        logger.error(f"Error during trade settlement: {e}")
        return {"settled": False, "error": str(e)}

    return {
        "settled": True,
        "settlement_results": settlement_results,
        "total_trades": len(order_dict["trades"]),
        "successful_settlements": sum(
            1 for r in settlement_results if r["settlement_result"]["success"]
        ),
    }


@app.post("/api/register_order")
async def register_order(payload: str = Form(...)):
    try:
        payload_json = json.loads(payload)
        symbol = "%s_%s" % (payload_json["baseAsset"], payload_json["quoteAsset"])

        # Step 1: Validate order prerequisites (balance and allowance)
        logger.info(f"Validating prerequisites for order: {payload_json}")
        validation_result = await validate_order_prerequisites(payload_json)

        if not validation_result["valid"]:
            logger.warning(f"Order validation failed: {validation_result}")
            return JSONResponse(
                content={
                    "message": "Order validation failed",
                    "errors": validation_result.get("errors", []),
                    "validation_details": validation_result.get("checks", {}),
                    "status_code": 0,
                },
                status_code=400,
            )

        logger.info(f"Order validation passed: {validation_result['checks']}")

        # Step 2: Process the order in the order book
        if symbol not in order_books:
            order_books[symbol] = OrderBook()

        order_book = order_books[symbol]

        _order = {
            "type": "limit",
            "trade_id": payload_json["account"],
            "account": payload_json["account"],
            "price": Decimal(payload_json["price"]),
            "quantity": Decimal(payload_json["quantity"]),
            "side": payload_json["side"],
            "baseAsset": payload_json["baseAsset"],
            "quoteAsset": payload_json["quoteAsset"],
            "private_key": payload_json["privateKey"]
        }

        process_result = order_book.process_order(_order, False, False)

        # This is the Failure case
        if not process_result["success"]:
            return JSONResponse(
                content={"message": process_result["data"], "status_code": 0},
                status_code=400,
            )

        trades, order, task_id, next_best_order = process_result["data"]

        if order is None:
            order = _order.copy()
            order["order_id"] = 1

        assert order is not None

        # Convert trades to the expected format
        converted_trades = []
        for trade in trades:
            party1 = [
                trade["party1"][0],
                trade["party1"][1],
                int(trade["party1"][2]) if trade["party1"][2] is not None else None,
                float(trade["party1"][3]) if trade["party1"][3] is not None else None,
                trade["party1"][4]
            ]
            party2 = [
                trade["party2"][0],
                trade["party2"][1],
                int(trade["party2"][2]) if trade["party2"][2] is not None else None,
                float(trade["party2"][3]) if trade["party2"][3] is not None else None,
                trade["party2"][4]

            ]

            converted_trade = {
                "timestamp": int(trade["timestamp"]),
                "price": float(trade["price"]),
                "quantity": float(trade["quantity"]),
                "time": int(trade["time"]),
                "party1": party1,
                "party2": party2,
            }
            converted_trades.append(converted_trade)

        # Convert order to a serializable format
        order_dict = {
            "orderId": int(order["order_id"]),
            "account": order["account"],
            "price": float(order["price"]),
            "quantity": float(order["quantity"]),
            "side": order["side"],
            "baseAsset": order["baseAsset"],
            "quoteAsset": order["quoteAsset"],
            "trade_id": order["trade_id"],
            "trades": converted_trades,
            "isValid": True if order["order_id"] != 0 else True,
            "timestamp": order["timestamp"],
        }

        next_best_order_dict = None
        if next_best_order is not None:
            next_best_order_dict = {
                "orderId": int(next_best_order.order_id),
                "account": next_best_order.account,
                "price": float(next_best_order.price),
                "quantity": float(next_best_order.quantity),
                "side": next_best_order.side,
                "baseAsset": next_best_order.baseAsset,
                "quoteAsset": next_best_order.quoteAsset,
                "trade_id": next_best_order.trade_id,
                "trades": [],
                "isValid": True if next_best_order.order_id != 0 else True,
                "timestamp": next_best_order.timestamp,
            }

        # Step 3: Settle trades if any exist
        settlement_info = {"settled": False}
        if converted_trades:
            logger.info(f"Attempting to settle {len(converted_trades)} trade(s)")
            settlement_info = await settle_trades_if_any(order_dict)
            logger.info(f"Settlement result: {settlement_info}")

        logger.info(f"Order processed successfully with {len(converted_trades)} trades")

        return JSONResponse(
            content={
                "message": "Order registered successfully",
                "order": order_dict,
                "nextBest": next_best_order_dict,
                "taskId": task_id,
                "validation_details": validation_result.get("checks", {}),
                "settlement_info": settlement_info,
                "status_code": 1,
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error in register_order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cancel_order")
def cancel_order(payload: str = Form(...)):
    try:
        payload_json = json.loads(payload)
        order_id = payload_json["orderId"]
        side = payload_json["side"]
        symbol = "%s_%s" % (payload_json["baseAsset"], payload_json["quoteAsset"])

        order_book = order_books[symbol]
        order = (
            order_book.bids.get_order(order_id)
            if order_id in order_book.bids.order_map
            else order_book.asks.get_order(order_id)
        )
        order_book.cancel_order(side, order_id)

        # Convert order to a serializable format
        order_dict = {
            "orderId": int(order_id),
            "account": order.account,
            "price": float(order.price),
            "quantity": float(order.quantity),
            "side": order.side,
            "baseAsset": order.baseAsset,
            "quoteAsset": order.quoteAsset,
            "trade_id": order.trade_id,
            "trades": [],
            "isValid": False,
            "timestamp": order.timestamp,
        }

        return JSONResponse(
            content={
                "message": "Order cancelled successfully",
                "order": order_dict,
                "status_code": 1,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/order")
def get_order(payload: str = Form(...)):
    try:
        payload_json = json.loads(payload)
        order_id = payload_json["orderId"]

        order = None
        for symbol, order_book in order_books.items():
            if (
                order_id in order_book.bids.order_map
                or order_id in order_book.asks.order_map
            ):
                order = (
                    order_book.bids.get_order(order_id)
                    if order_id in order_book.bids.order_map
                    else order_book.asks.get_order(order_id)
                )

        if order is not None:
            order_dict = {
                "orderId": int(order.order_id) if order.order_id is not None else None,
                "account": order.account,
                "price": float(order.price),
                "quantity": float(order.quantity),
                "side": order.side,
                "baseAsset": order.baseAsset,
                "quoteAsset": order.quoteAsset,
                "trade_id": order.trade_id,
                "trades": [],
                "isValid": True if order.order_id is not None else False,
                "timestamp": order.timestamp,
            }

            return JSONResponse(
                content={
                    "message": "Order retrieved successfully",
                    "order": order_dict,
                    "status_code": 1,
                }
            )
        else:
            return JSONResponse(
                content={"message": "Order not found", "order": None, "status_code": 0}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/orderbook")
def get_orderbook(payload: str = Form(...)):
    try:
        payload_json = json.loads(payload)
        symbol = payload_json["symbol"]

        if symbol not in order_books:
            order_book = OrderBook()
            order_books[symbol] = order_book
        else:
            order_book = order_books[symbol]

        result = order_book.get_orderbook(payload_json["symbol"])

        return JSONResponse(
            content={
                "message": "Order book retrieved successfully",
                "orderbook": result,
                "status_code": 1,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/get_best_order")
def get_best_order(payload: str = Form(...)):
    try:
        payload_json = json.loads(payload)
        symbol = "%s_%s" % (payload_json["baseAsset"], payload_json["quoteAsset"])
        side = payload_json["side"]

        if symbol not in order_books:
            raise HTTPException(status_code=404, detail="Order book not found")

        order_book = order_books[symbol]
        price = (
            order_book.get_best_bid() if side == "bid" else order_book.get_best_ask()
        )
        if price is None:
            # no bid or ask order
            # fake content
            return JSONResponse(
                content={
                    "message": "no bid or ask order",
                    "order": {
                        "order_id": 1234567890,
                        "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                        "price": 0,
                        "quantity": 0,
                        "side": side,
                        "baseAsset": payload_json["baseAsset"],
                        "quoteAsset": payload_json["quoteAsset"],
                        "trade_id": None,
                        "trades": [],
                        "isValid": False,
                        "timestamp": int(time.time() * 1000),
                    },
                }
            )

        price_list = (
            order_book.bids.price_map[price]
            if side == "bid"
            else order_book.asks.price_map[price]
        )
        current_order = price_list.head_order
        order_dict = {
            "order_id": int(current_order.order_id),
            "account": current_order.account,
            "price": float(current_order.price),
            "quantity": float(current_order.quantity),
            "side": current_order.side,
            "baseAsset": current_order.baseAsset,
            "quoteAsset": current_order.quoteAsset,
            "trade_id": current_order.trade_id,
            "trades": [],
            "isValid": True,
            "timestamp": current_order.timestamp,
        }

        return JSONResponse(
            content={
                "message": "Best order retrieved successfully",
                "order": order_dict,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/check_available_funds")
def check_available_funds(payload: str = Form(...)):
    try:
        payload_json = json.loads(payload)
        account = payload_json["account"]
        asset = payload_json["asset"]

        # Calculate total locked funds across all order books
        total_locked_amount = Decimal("0")

        # Iterate through all order books
        for symbol, order_book in order_books.items():
            # Check if this order book involves the asset we're looking for
            base_asset, quote_asset = symbol.split("_")

            # Check bids (buying orders)
            if quote_asset == asset:  # If quote asset matches, check bids
                for order_id, order in order_book.bids.order_map.items():
                    if order["account"].lower() == account.lower():
                        # For bids, the locked amount is price * quantity in quote asset
                        locked_amount = order["price"] * order["quantity"]
                        total_locked_amount += locked_amount

            # Check asks (selling orders)
            if base_asset == asset:  # If base asset matches, check asks
                for order_id, order in order_book.asks.order_map.items():
                    if order["account"].lower() == account.lower():
                        # For asks, the locked amount is just the quantity in base asset
                        total_locked_amount += order["quantity"]

        return JSONResponse(
            content={
                "message": "Available funds checked successfully",
                "account": account,
                "asset": asset,
                "lockedAmount": float(total_locked_amount),
                "status_code": 1,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Add a health check endpoint for the settlement system
@app.get("/api/settlement_health")
async def settlement_health():
    """Check if settlement system is operational"""
    try:
        if not settlement_client:
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "message": "Settlement client not initialized",
                    "web3_connected": False,
                },
                status_code=503,
            )

        # Check if web3 is connected
        web3_connected = settlement_client.web3.isConnected()

        return JSONResponse(
            content={
                "status": "healthy" if web3_connected else "degraded",
                "message": (
                    "Settlement system operational"
                    if web3_connected
                    else "Web3 connection issues"
                ),
                "web3_connected": web3_connected,
                "contract_address": CONTRACT_ADDRESS,
            },
            status_code=200 if web3_connected else 503,
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "message": f"Settlement health check failed: {str(e)}",
                "web3_connected": False,
            },
            status_code=503,
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
