from web3 import Web3
from eth_account import Account

# from eth_account.messages import encode_structured_data
# import json
# import time
from typing import Dict, List, Tuple


class TradeSettlementClient:
    def __init__(
        self,
        web3_provider: str,
        contract_address: str,
        contract_abi: dict,
        private_key: str = None,
    ):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.contract = self.web3.eth.contract(
            address=self.contract_address, abi=contract_abi
        )
        self.account = Account.from_key(private_key) if private_key else None

    def check_allowance(
        self, user_address: str, token_address: str, required_amount: int
    ) -> Tuple[bool, int]:
        """Check if user has sufficient allowance for the contract"""
        try:
            user_address = Web3.to_checksum_address(user_address)
            token_address = Web3.to_checksum_address(token_address)

            result = self.contract.functions.checkAllowance(
                user_address, token_address, required_amount
            ).call()
            sufficient, current_allowance = result
            # print(sufficient, current_allowance, "CHEK HERe")

            return sufficient, current_allowance

        except Exception as e:
            print(f"Error checking allowance: {e}")
            return False, 0

    def check_balance(
        self, user_address: str, token_address: str, required_amount: int
    ) -> Tuple[bool, int]:
        """Check if user has sufficient token balance"""
        try:
            user_address = Web3.to_checksum_address(user_address)
            token_address = Web3.to_checksum_address(token_address)

            result = self.contract.functions.checkBalance(
                user_address, token_address, required_amount
            ).call()

            sufficient, current_balance = result

            # print(sufficient, current_balance, "WHO BE YOU!")
            return sufficient, current_balance

        except Exception as e:
            print(f"Error checking balance: {e}")
            return False, 0

    def batch_check_allowances(
        self, users: List[str], tokens: List[str], amounts: List[int]
    ) -> Tuple[List[bool], List[int]]:
        """Batch check allowances for multiple users and tokens"""
        try:
            users_checksummed = [Web3.to_checksum_address(addr) for addr in users]
            tokens_checksummed = [Web3.to_checksum_address(addr) for addr in tokens]

            result = self.contract.functions.batchCheckAllowances(
                users_checksummed, tokens_checksummed, amounts
            ).call()

            sufficient_list, allowances_list = result
            return list(sufficient_list), list(allowances_list)

        except Exception as e:
            print(f"Error in batch checking allowances: {e}")
            return [], []

    def create_trade_signature(
        self,
        user_private_key: str,
        order_id: int,
        base_asset: str,
        quote_asset: str,
        price: int,
        quantity: int,
        side: str,
        timestamp: int,
        nonce: int,
    ) -> str:
        """Create a signature for a trade order using the exact format from your contract"""
        try:
            # Create the message hash exactly as in your contract
            message_hash = Web3.keccak(
                encode_abi_packed(
                    [
                        "uint256",
                        "address",
                        "address",
                        "uint256",
                        "uint256",
                        "string",
                        "uint256",
                        "uint256",
                    ],
                    [
                        order_id,
                        Web3.to_checksum_address(base_asset),
                        Web3.to_checksum_address(quote_asset),
                        price,
                        quantity,
                        side,
                        timestamp,
                        nonce,
                    ],
                )
            )

            # Sign the message using the user's private key
            account = Account.from_key(user_private_key)
            print(account.address, "ADDRESSA")

            # Create the Ethereum signed message hash (adds the prefix)
            eth_message_hash = encode_defunct(message_hash)

            # Sign the hash
            signature = account.sign_message(eth_message_hash)

            return signature.signature.hex()

        except Exception as e:
            print(f"Error creating signature: {e}")
            return ""

    def verify_trade_signature(
        self,
        signer: str,
        order_id: int,
        base_asset: str,
        quote_asset: str,
        price: int,
        quantity: int,
        side: str,
        timestamp: int,
        nonce: int,
        signature: str,
    ) -> bool:
        """Verify a trade signature on-chain"""
        try:
            result = self.contract.functions.verifyTradeSignature(
                Web3.to_checksum_address(signer),
                order_id,
                Web3.to_checksum_address(base_asset),
                Web3.to_checksum_address(quote_asset),
                price,
                quantity,
                side,
                timestamp,
                nonce,
                bytes.fromhex(signature.replace("0x", "")),
            ).call()

            return result

        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False

    def get_user_nonce(self, user_address: str, token_address: str) -> int:
        """Get user's current nonce for a specific token"""
        try:
            user_address = Web3.to_checksum_address(user_address)
            token_address = Web3.to_checksum_address(token_address)

            nonce = self.contract.functions.getUserNonce(
                user_address, token_address
            ).call()
            return nonce

        except Exception as e:
            print(f"Error getting nonce: {e}")
            return 0

    def settle_trade_direct(
        self,
        trade_execution_tuple: tuple,
        party1: str,
        party2: str,
        party1_quantity: int,
        party2_quantity: int,
        party1_side: str,
        party2_side: str,
        signature1: str,
        signature2: str,
        nonce1: int,
        nonce2: int,
    ) -> dict:
        """Settle a trade directly using the contract's settleTrade function"""
        if not self.account:
            raise ValueError("No private key provided for transaction signing")

        try:
            # Build the transaction using the exact function signature from your contract
            function = self.contract.functions.settleTrade(
                trade_execution_tuple,  # TradeExecution struct as tuple
                Web3.to_checksum_address(party1),
                Web3.to_checksum_address(party2),
                party1_quantity,
                party2_quantity,
                party1_side,
                party2_side,
                bytes.fromhex(signature1.replace("0x", "")),
                bytes.fromhex(signature2.replace("0x", "")),
                nonce1,
                nonce2,
            )

            # Estimate gas
            gas_estimate = function.estimateGas({"from": self.account.address})

            # Build transaction
            transaction = function.build_transaction(
                {
                    "from": self.account.address,
                    "gas": int(gas_estimate * 1.2),  # Add 20% buffer
                    "gasPrice": self.web3.toWei("20", "gwei"),
                    "nonce": self.web3.eth.get_transaction_count(self.account.address),
                }
            )

            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction, self.account.key
            )
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            return {
                "success": receipt.status == 1,
                "transaction_hash": receipt.transactionHash.hex(),
                "gas_used": receipt.gasUsed,
                "block_number": receipt.blockNumber,
            }

        except Exception as e:
            print(f"Error settling trade: {e}")
            return {"success": False, "error": str(e)}

    def get_token_address(self, token_symbol: str) -> str:
        """Get token contract address from symbol"""
        # You should implement your own mapping or load from environment
        token_addresses = {
            "SEI": "0x1234567890123456789012345678901234567890",  # Replace with actual SEI token address
            "USDT": "0x0987654321098765432109876543210987654321",  # Replace with actual USDT token address
        }
        return token_addresses.get(token_symbol.upper(), token_symbol)

    def validate_trade_prerequisites(self, trade_data: dict) -> dict:
        """Validate all prerequisites before settling a trade"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "allowance_checks": {},
            "balance_checks": {},
        }

        try:
            # Extract trade information
            if not trade_data.get("trades") or len(trade_data["trades"]) == 0:
                return results  # No trades to validate

            trade = trade_data["trades"][0]  # Validate first trade
            party1 = trade["party1"][0]  # Address
            party2 = trade["party2"][0]  # Address
            party1_side = trade["party1"][1]  # Side
            party2_side = trade["party2"][1]  # Side

            base_asset_addr = self.get_token_address(trade_data["baseAsset"])
            quote_asset_addr = self.get_token_address(trade_data["quoteAsset"])

            quantity = trade_data["quantity"]
            price = trade_data["price"]

            # Convert to wei (18 decimals)
            base_amount = int(quantity * (10**18))
            quote_amount = int(quantity * price * (10**18))

            # Check party1 requirements
            if party1_side == "bid":
                # Bidder needs quote asset allowance and balance
                quote_sufficient, quote_allowance = self.check_allowance(
                    party1, quote_asset_addr, quote_amount
                )
                quote_bal_sufficient, quote_balance = self.check_balance(
                    party1, quote_asset_addr, quote_amount
                )

                results["allowance_checks"]["party1_quote"] = {
                    "sufficient": quote_sufficient,
                    "current": quote_allowance,
                    "required": quote_amount,
                }
                results["balance_checks"]["party1_quote"] = {
                    "sufficient": quote_bal_sufficient,
                    "current": quote_balance,
                    "required": quote_amount,
                }

                if not quote_sufficient:
                    results["errors"].append(
                        f"Party1 insufficient quote allowance: {quote_allowance} < {quote_amount}"
                    )
                    results["valid"] = False

                if not quote_bal_sufficient:
                    results["errors"].append(
                        f"Party1 insufficient quote balance: {quote_balance} < {quote_amount}"
                    )
                    results["valid"] = False

            else:  # ask
                # Asker needs base asset allowance and balance
                base_sufficient, base_allowance = self.check_allowance(
                    party1, base_asset_addr, base_amount
                )
                base_bal_sufficient, base_balance = self.check_balance(
                    party1, base_asset_addr, base_amount
                )

                results["allowance_checks"]["party1_base"] = {
                    "sufficient": base_sufficient,
                    "current": base_allowance,
                    "required": base_amount,
                }
                results["balance_checks"]["party1_base"] = {
                    "sufficient": base_bal_sufficient,
                    "current": base_balance,
                    "required": base_amount,
                }

                if not base_sufficient:
                    results["errors"].append(
                        f"Party1 insufficient base allowance: {base_allowance} < {base_amount}"
                    )
                    results["valid"] = False

                if not base_bal_sufficient:
                    results["errors"].append(
                        f"Party1 insufficient base balance: {base_balance} < {base_amount}"
                    )
                    results["valid"] = False

            # Check party2 requirements (opposite of party1)
            if party2_side == "bid":
                # Bidder needs quote asset allowance and balance
                quote_sufficient, quote_allowance = self.check_allowance(
                    party2, quote_asset_addr, quote_amount
                )
                quote_bal_sufficient, quote_balance = self.check_balance(
                    party2, quote_asset_addr, quote_amount
                )

                results["allowance_checks"]["party2_quote"] = {
                    "sufficient": quote_sufficient,
                    "current": quote_allowance,
                    "required": quote_amount,
                }
                results["balance_checks"]["party2_quote"] = {
                    "sufficient": quote_bal_sufficient,
                    "current": quote_balance,
                    "required": quote_amount,
                }

                if not quote_sufficient:
                    results["errors"].append(
                        f"Party2 insufficient quote allowance: {quote_allowance} < {quote_amount}"
                    )
                    results["valid"] = False

                if not quote_bal_sufficient:
                    results["errors"].append(
                        f"Party2 insufficient quote balance: {quote_balance} < {quote_amount}"
                    )
                    results["valid"] = False

            else:  # ask
                # Asker needs base asset allowance and balance
                base_sufficient, base_allowance = self.check_allowance(
                    party2, base_asset_addr, base_amount
                )
                base_bal_sufficient, base_balance = self.check_balance(
                    party2, base_asset_addr, base_amount
                )

                results["allowance_checks"]["party2_base"] = {
                    "sufficient": base_sufficient,
                    "current": base_allowance,
                    "required": base_amount,
                }
                results["balance_checks"]["party2_base"] = {
                    "sufficient": base_bal_sufficient,
                    "current": base_balance,
                    "required": base_amount,
                }

                if not base_sufficient:
                    results["errors"].append(
                        f"Party2 insufficient base allowance: {base_allowance} < {base_amount}"
                    )
                    results["valid"] = False

                if not base_bal_sufficient:
                    results["errors"].append(
                        f"Party2 insufficient base balance: {base_balance} < {base_amount}"
                    )
                    results["valid"] = False

            return results

        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Error validating prerequisites: {e}")
            return results


# Contract ABI for your TradeSettlement contract
TRADE_SETTLEMENT_ABI = [
    {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "OwnableInvalidOwner",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "OwnableUnauthorizedAccount",
        "type": "error",
    },
    {"inputs": [], "name": "ReentrancyGuardReentrantCall", "type": "error"},
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "token",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "allowance",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "required",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "bool",
                "name": "sufficient",
                "type": "bool",
            },
        ],
        "name": "AllowanceChecked",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "previousOwner",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "newOwner",
                "type": "address",
            },
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "party1",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "party2",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "baseAsset",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "quoteAsset",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "price",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "quantity",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
        ],
        "name": "TradeSettled",
        "type": "event",
    },
    {
        "inputs": [
            {"internalType": "address[]", "name": "users", "type": "address[]"},
            {"internalType": "address[]", "name": "tokens", "type": "address[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
        ],
        "name": "batchCheckAllowances",
        "outputs": [
            {"internalType": "bool[]", "name": "sufficient", "type": "bool[]"},
            {"internalType": "uint256[]", "name": "allowances", "type": "uint256[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "requiredAmount", "type": "uint256"},
        ],
        "name": "checkAllowance",
        "outputs": [
            {"internalType": "bool", "name": "sufficient", "type": "bool"},
            {"internalType": "uint256", "name": "currentAllowance", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "requiredAmount", "type": "uint256"},
        ],
        "name": "checkBalance",
        "outputs": [
            {"internalType": "bool", "name": "sufficient", "type": "bool"},
            {"internalType": "uint256", "name": "currentBalance", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "executedTrades",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "address", "name": "token", "type": "address"},
        ],
        "name": "getUserNonce",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "address", "name": "", "type": "address"},
        ],
        "name": "nonces",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "renounceOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "uint256", "name": "orderId", "type": "uint256"},
                    {"internalType": "address", "name": "account", "type": "address"},
                    {"internalType": "uint256", "name": "price", "type": "uint256"},
                    {"internalType": "uint256", "name": "quantity", "type": "uint256"},
                    {"internalType": "string", "name": "side", "type": "string"},
                    {"internalType": "address", "name": "baseAsset", "type": "address"},
                    {
                        "internalType": "address",
                        "name": "quoteAsset",
                        "type": "address",
                    },
                    {"internalType": "string", "name": "tradeId", "type": "string"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {"internalType": "bool", "name": "isValid", "type": "bool"},
                ],
                "internalType": "struct TradeSettlement.TradeExecution",
                "name": "tradeData",
                "type": "tuple",
            },
            {"internalType": "address", "name": "party1", "type": "address"},
            {"internalType": "address", "name": "party2", "type": "address"},
            {"internalType": "uint256", "name": "party1Quantity", "type": "uint256"},
            {"internalType": "uint256", "name": "party2Quantity", "type": "uint256"},
            {"internalType": "string", "name": "party1Side", "type": "string"},
            {"internalType": "string", "name": "party2Side", "type": "string"},
            {"internalType": "bytes", "name": "signature1", "type": "bytes"},
            {"internalType": "bytes", "name": "signature2", "type": "bytes"},
            {"internalType": "uint256", "name": "nonce1", "type": "uint256"},
            {"internalType": "uint256", "name": "nonce2", "type": "uint256"},
        ],
        "name": "settleTrade",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "signer", "type": "address"},
            {"internalType": "uint256", "name": "orderId", "type": "uint256"},
            {"internalType": "address", "name": "baseAsset", "type": "address"},
            {"internalType": "address", "name": "quoteAsset", "type": "address"},
            {"internalType": "uint256", "name": "price", "type": "uint256"},
            {"internalType": "uint256", "name": "quantity", "type": "uint256"},
            {"internalType": "string", "name": "side", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "uint256", "name": "nonce", "type": "uint256"},
            {"internalType": "bytes", "name": "signature", "type": "bytes"},
        ],
        "name": "verifyTradeSignature",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "pure",
        "type": "function",
    },
]


# Helper function to encode ABI packed data
def encode_abi_packed(types, values):
    """Helper function to encode data similar to Solidity's abi.encodePacked"""
    from eth_abi.packed import encode_packed

    return encode_packed(types, values)


# Import required functions from eth_account
from eth_account.messages import encode_defunct


# Utility functions for allowance checking
class AllowanceChecker:
    def __init__(self, web3_provider: str):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))

        # Standard ERC20 ABI for allowance checking
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"},
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function",
            },
        ]

    def check_token_allowance(
        self, token_address: str, owner: str, spender: str
    ) -> int:
        """Direct ERC20 allowance check"""
        try:
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address), abi=self.erc20_abi
            )

            allowance = token_contract.functions.allowance(
                Web3.to_checksum_address(owner), Web3.to_checksum_address(spender)
            ).call()

            return allowance

        except Exception as e:
            print(f"Error checking token allowance: {e}")
            return 0

    def check_token_balance(self, token_address: str, owner: str) -> int:
        """Direct ERC20 balance check"""
        try:
            token_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address), abi=self.erc20_abi
            )

            balance = token_contract.functions.balanceOf(
                Web3.to_checksum_address(owner)
            ).call()

            return balance

        except Exception as e:
            print(f"Error checking token balance: {e}")
            return 0

    def batch_allowance_check(self, checks: List[Dict]) -> List[Dict]:
        """
        Batch check multiple allowances
        checks format: [{'token': '0x...', 'owner': '0x...', 'spender': '0x...', 'required': 1000}, ...]
        """
        results = []

        for check in checks:
            try:
                current_allowance = self.check_token_allowance(
                    check["token"], check["owner"], check["spender"]
                )

                current_balance = self.check_token_balance(
                    check["token"], check["owner"]
                )

                result = {
                    "token": check["token"],
                    "owner": check["owner"],
                    "spender": check["spender"],
                    "required": check["required"],
                    "current_allowance": current_allowance,
                    "current_balance": current_balance,
                    "allowance_sufficient": current_allowance >= check["required"],
                    "balance_sufficient": current_balance >= check["required"],
                }

                results.append(result)

            except Exception as e:
                results.append(
                    {
                        "token": check["token"],
                        "owner": check["owner"],
                        "spender": check["spender"],
                        "error": str(e),
                    }
                )

        return results


# Example usage and configuration
def create_settlement_client(
    web3_provider: str, contract_address: str, private_key: str = None
):
    """Factory function to create a TradeSettlementClient with the correct ABI"""
    return TradeSettlementClient(
        web3_provider=web3_provider,
        contract_address=contract_address,
        contract_abi=TRADE_SETTLEMENT_ABI,
        private_key=private_key,
    )


# Example usage
def main():
    # Configuration
    WEB3_PROVIDER = "https://your-ethereum-node.com"
    CONTRACT_ADDRESS = "0x1234567890123456789012345678901234567890"
    PRIVATE_KEY = "your-private-key"

    # Initialize client
    client = create_settlement_client(WEB3_PROVIDER, CONTRACT_ADDRESS, PRIVATE_KEY)

    # Test basic functionality
    try:
        # Check if client is connected
        print(f"Web3 connected: {client.web3.isConnected()}")

        # Test allowance check
        test_user = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92367"
        test_token = "0x1234567890123456789012345678901234567890"
        test_amount = 1000000000000000000  # 1 token with 18 decimals

        sufficient, current = client.check_allowance(test_user, test_token, test_amount)
        print(f"Allowance check - Sufficient: {sufficient}, Current: {current}")

        # Test balance check
        balance_sufficient, current_balance = client.check_balance(
            test_user, test_token, test_amount
        )
        print(
            f"Balance check - Sufficient: {balance_sufficient}, Current: {current_balance}"
        )

        # Get nonce
        nonce = client.get_user_nonce(test_user, test_token)
        print(f"User nonce: {nonce}")

    except Exception as e:
        print(f"Error during testing: {e}")


if __name__ == "__main__":
    main()
