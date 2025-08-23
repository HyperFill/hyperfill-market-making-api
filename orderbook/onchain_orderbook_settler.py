from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_structured_data
import json
import time
from typing import Dict, List, Tuple, Optional

class TradeSettlementClient:
    def __init__(self, web3_provider: str, contract_address: str, contract_abi: dict, private_key: str = None):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.contract_address = Web3.toChecksumAddress(contract_address)
        self.contract = self.web3.eth.contract(address=self.contract_address, abi=contract_abi)
        self.account = Account.from_key(private_key) if private_key else None
        
    def check_allowance(self, user_address: str, token_address: str, required_amount: int) -> Tuple[bool, int]:
        """Check if user has sufficient allowance for the contract"""
        try:
            user_address = Web3.toChecksumAddress(user_address)
            token_address = Web3.toChecksumAddress(token_address)
            
            result = self.contract.functions.checkAllowance(
                user_address,
                token_address,
                required_amount
            ).call()
            
            sufficient, current_allowance = result
            return sufficient, current_allowance
            
        except Exception as e:
            print(f"Error checking allowance: {e}")
            return False, 0
    
    def check_balance(self, user_address: str, token_address: str, required_amount: int) -> Tuple[bool, int]:
        """Check if user has sufficient token balance"""
        try:
            user_address = Web3.toChecksumAddress(user_address)
            token_address = Web3.toChecksumAddress(token_address)
            
            result = self.contract.functions.checkBalance(
                user_address,
                token_address,
                required_amount
            ).call()
            
            sufficient, current_balance = result
            return sufficient, current_balance
            
        except Exception as e:
            print(f"Error checking balance: {e}")
            return False, 0
    
    def batch_check_allowances(self, users: List[str], tokens: List[str], amounts: List[int]) -> Tuple[List[bool], List[int]]:
        """Batch check allowances for multiple users and tokens"""
        try:
            users_checksummed = [Web3.toChecksumAddress(addr) for addr in users]
            tokens_checksummed = [Web3.toChecksumAddress(addr) for addr in tokens]
            
            result = self.contract.functions.batchCheckAllowances(
                users_checksummed,
                tokens_checksummed,
                amounts
            ).call()
            
            sufficient_list, allowances_list = result
            return list(sufficient_list), list(allowances_list)
            
        except Exception as e:
            print(f"Error in batch checking allowances: {e}")
            return [], []
    
    def create_trade_signature(self, order_id: int, base_asset: str, quote_asset: str, 
                             price: int, quantity: int, side: str, timestamp: int, 
                             nonce: int, private_key: str) -> str:
        """Create a signature for a trade order"""
        try:
            # Create message hash
            message_hash = Web3.keccak(
                ["uint256", "address", "address", "uint256", "uint256", "string", "uint256", "uint256"],
                [order_id, base_asset, quote_asset, price, quantity, side, timestamp, nonce]
            )
            
            # Sign the message
            account = Account.from_key(private_key)
            signature = account.signHash(message_hash)
            
            return signature.signature.hex()
            
        except Exception as e:
            print(f"Error creating signature: {e}")
            return ""
    
    def verify_trade_signature(self, signer: str, order_id: int, base_asset: str, 
                             quote_asset: str, price: int, quantity: int, side: str, 
                             timestamp: int, nonce: int, signature: str) -> bool:
        """Verify a trade signature on-chain"""
        try:
            result = self.contract.functions.verifyTradeSignature(
                Web3.toChecksumAddress(signer),
                order_id,
                Web3.toChecksumAddress(base_asset),
                Web3.toChecksumAddress(quote_asset),
                price,
                quantity,
                side,
                timestamp,
                nonce,
                bytes.fromhex(signature.replace('0x', ''))
            ).call()
            
            return result
            
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False
    
    def get_user_nonce(self, user_address: str, token_address: str) -> int:
        """Get user's current nonce for a specific token"""
        try:
            user_address = Web3.toChecksumAddress(user_address)
            token_address = Web3.toChecksumAddress(token_address)
            
            nonce = self.contract.functions.getUserNonce(user_address, token_address).call()
            return nonce
            
        except Exception as e:
            print(f"Error getting nonce: {e}")
            return 0
    
    def settle_trade(self, trade_data: dict, party1: str, party2: str, 
                    party1_quantity: int, party2_quantity: int, party1_side: str, 
                    party2_side: str, signature1: str, signature2: str, 
                    nonce1: int, nonce2: int) -> dict:
        """Settle a trade on-chain"""
        if not self.account:
            raise ValueError("No private key provided for transaction signing")
        
        try:
            # Prepare trade execution struct
            trade_execution = (
                trade_data['orderId'],
                Web3.toChecksumAddress(trade_data['account']),
                int(trade_data['price'] * 1e18),  # Convert to wei-like units
                trade_data['quantity'],
                trade_data['side'],
                Web3.toChecksumAddress(self.get_token_address(trade_data['baseAsset'])),
                Web3.toChecksumAddress(self.get_token_address(trade_data['quoteAsset'])),
                trade_data['trade_id'],
                trade_data['timestamp'],
                trade_data['isValid']
            )
            
            # Build transaction
            function = self.contract.functions.settleTrade(
                trade_execution,
                Web3.toChecksumAddress(party1),
                Web3.toChecksumAddress(party2),
                party1_quantity,
                party2_quantity,
                party1_side,
                party2_side,
                bytes.fromhex(signature1.replace('0x', '')),
                bytes.fromhex(signature2.replace('0x', '')),
                nonce1,
                nonce2
            )
            
            # Estimate gas
            gas_estimate = function.estimateGas({'from': self.account.address})
            
            # Build transaction
            transaction = function.buildTransaction({
                'from': self.account.address,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': self.web3.toWei('20', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': receipt.status == 1,
                'transaction_hash': receipt.transactionHash.hex(),
                'gas_used': receipt.gasUsed,
                'block_number': receipt.blockNumber
            }
            
        except Exception as e:
            print(f"Error settling trade: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_token_address(self, token_symbol: str) -> str:
        """Get token contract address from symbol (you should implement your own mapping)"""
        token_addresses = {
            'SEI': '0x1234567890123456789012345678901234567890',  # Replace with actual SEI token address
            'USDT': '0x0987654321098765432109876543210987654321',  # Replace with actual USDT token address
        }
        return token_addresses.get(token_symbol.upper(), token_symbol)
    
    def validate_trade_prerequisites(self, trade_data: dict) -> dict:
        """Validate all prerequisites before settling a trade"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'allowance_checks': {},
            'balance_checks': {}
        }
        
        try:
            # Extract trade information
            party1 = trade_data['trades'][0]['party1'][0]  # Address
            party2 = trade_data['trades'][0]['party2'][0]  # Address
            
            base_asset_addr = self.get_token_address(trade_data['baseAsset'])
            quote_asset_addr = self.get_token_address(trade_data['quoteAsset'])
            
            quantity = trade_data['quantity']
            price = trade_data['price']
            quote_amount = int(quantity * price * 1e18)  # Convert to proper units
            
            # Check party1 (bidder) allowances and balances
            if trade_data['trades'][0]['party1'][1] == 'bid':  # Party1 is bidder
                # Bidder needs USDT allowance and balance
                usdt_sufficient, usdt_allowance = self.check_allowance(party1, quote_asset_addr, quote_amount)
                usdt_bal_sufficient, usdt_balance = self.check_balance(party1, quote_asset_addr, quote_amount)
                
                results['allowance_checks']['party1_quote'] = {
                    'sufficient': usdt_sufficient,
                    'current': usdt_allowance,
                    'required': quote_amount
                }
                results['balance_checks']['party1_quote'] = {
                    'sufficient': usdt_bal_sufficient,
                    'current': usdt_balance,
                    'required': quote_amount
                }
                
                if not usdt_sufficient:
                    results['errors'].append(f"Party1 insufficient USDT allowance: {usdt_allowance} < {quote_amount}")
                    results['valid'] = False
                
                if not usdt_bal_sufficient:
                    results['errors'].append(f"Party1 insufficient USDT balance: {usdt_balance} < {quote_amount}")
                    results['valid'] = False
                
                # Check party2 (asker) SEI allowance and balance
                sei_amount = quantity * 1e18  # Assuming 18 decimals for SEI
                sei_sufficient, sei_allowance = self.check_allowance(party2, base_asset_addr, sei_amount)
                sei_bal_sufficient, sei_balance = self.check_balance(party2, base_asset_addr, sei_amount)
                
                results['allowance_checks']['party2_base'] = {
                    'sufficient': sei_sufficient,
                    'current': sei_allowance,
                    'required': sei_amount
                }
                results['balance_checks']['party2_base'] = {
                    'sufficient': sei_bal_sufficient,
                    'current': sei_balance,
                    'required': sei_amount
                }
                
                if not sei_sufficient:
                    results['errors'].append(f"Party2 insufficient SEI allowance: {sei_allowance} < {sei_amount}")
                    results['valid'] = False
                
                if not sei_bal_sufficient:
                    results['errors'].append(f"Party2 insufficient SEI balance: {sei_balance} < {sei_amount}")
                    results['valid'] = False
            
            return results
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Error validating prerequisites: {e}")
            return results


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
                    {"name": "spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
    
    def check_token_allowance(self, token_address: str, owner: str, spender: str) -> int:
        """Direct ERC20 allowance check"""
        try:
            token_contract = self.web3.eth.contract(
                address=Web3.toChecksumAddress(token_address),
                abi=self.erc20_abi
            )
            
            allowance = token_contract.functions.allowance(
                Web3.toChecksumAddress(owner),
                Web3.toChecksumAddress(spender)
            ).call()
            
            return allowance
            
        except Exception as e:
            print(f"Error checking token allowance: {e}")
            return 0
    
    def check_token_balance(self, token_address: str, owner: str) -> int:
        """Direct ERC20 balance check"""
        try:
            token_contract = self.web3.eth.contract(
                address=Web3.toChecksumAddress(token_address),
                abi=self.erc20_abi
            )
            
            balance = token_contract.functions.balanceOf(
                Web3.toChecksumAddress(owner)
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
                    check['token'],
                    check['owner'],
                    check['spender']
                )
                
                current_balance = self.check_token_balance(
                    check['token'],
                    check['owner']
                )
                
                result = {
                    'token': check['token'],
                    'owner': check['owner'],
                    'spender': check['spender'],
                    'required': check['required'],
                    'current_allowance': current_allowance,
                    'current_balance': current_balance,
                    'allowance_sufficient': current_allowance >= check['required'],
                    'balance_sufficient': current_balance >= check['required']
                }
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'token': check['token'],
                    'owner': check['owner'],
                    'spender': check['spender'],
                    'error': str(e)
                })
        
        return results


# Example usage
def main():
    # Configuration
    WEB3_PROVIDER = "https://your-ethereum-node.com"
    CONTRACT_ADDRESS = "0x1234567890123456789012345678901234567890"
    PRIVATE_KEY = "your-private-key"
    
    # Contract ABI (you'll need to include the full ABI)
    CONTRACT_ABI = []  # Include your contract ABI here
    
    # Initialize client
    client = TradeSettlementClient(WEB3_PROVIDER, CONTRACT_ADDRESS, CONTRACT_ABI, PRIVATE_KEY)
    
    # Your trade data from the API response
    trade_data = {
        "orderId": 0,
        "account": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92367",
        "price": 0.32,
        "quantity": 20,
        "side": "ask",
        "baseAsset": "SEI",
        "quoteAsset": "USDT",
        "trade_id": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92367",
        "trades": [
            {
                "timestamp": 1755931666735,
                "price": 0.32,
                "quantity": 20,
                "time": 1755931666735,
                "party1": ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92267", "bid", 1, 25],
                "party2": ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92367", "ask", None, None]
            }
        ],
        "isValid": False,
        "timestamp": 1755931666735
    }
    
    # Validate prerequisites
    validation_result = client.validate_trade_prerequisites(trade_data)
    
    if not validation_result['valid']:
        print("Trade validation failed:")
        for error in validation_result['errors']:
            print(f"  - {error}")
        return
    
    print("Trade validation passed!")
    print("Allowance checks:", validation_result['allowance_checks'])
    print("Balance checks:", validation_result['balance_checks'])
    
    # If validation passes, you can proceed with settlement
    # (You'll need to implement signature generation for both parties)

if __name__ == "__main__":
    main()