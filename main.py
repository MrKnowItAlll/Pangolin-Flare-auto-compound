import os
import time
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

# Flare RPC connection
rpcurl = "https://flare-api.flare.network/ext/C/rpc"
web3 = Web3(Web3.HTTPProvider(rpcurl))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

seconds_in_year = 60 * 60 * 24 * 365
# Position settings
position_id = 814
compound_above = 5


def read_json(path):
    with open(path) as json_file:
        return json.load(json_file)


# pangolin staking positions
pangolinContractAddress = '0x12245B3Fe351ec3BE15EF971f31927Af1292Ff40'
pangolinABI = read_json("pangolin_abi.json")
pangolinContract = web3.eth.contract(address=Web3.toChecksumAddress(pangolinContractAddress), abi=pangolinABI)


def transact(web3, account, tx):
    print("transact nonce:{}".format(tx['nonce']))
    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    time.sleep(1)
    return tx_receipt


def compound(web3, account):
    tx_parms = {
        'chainId': 14,
        'gas': 500000,
        'gasPrice': web3.toWei('50', 'gwei'),
        'nonce': web3.eth.getTransactionCount(account.address)
    }
    tx = pangolinContract.functions.compound(position_id).buildTransaction(tx_parms)
    tx_reciept = transact(web3, account, tx)


if __name__ == '__main__':
    private_key = os.environ['KEY']
    account = Account.from_key(private_key)

    while True:
        # Get pending rewards
        rewards = Web3.fromWei(pangolinContract.functions.positionPendingRewards(position_id).call(), 'ether')

        # get position size
        position = Web3.fromWei(pangolinContract.functions.positions(position_id).call()[0][0], 'ether')

        print("Pangolin position: \x1b[35m{}\x1b[0m\nrewards_pending: \x1b[31m{}\x1b[0m".format(position, rewards))

        # get APR
        reward_rate = Web3.fromWei(pangolinContract.functions.positionRewardRate(position_id).call(),
                                   'ether') * seconds_in_year
        apr = round((reward_rate / position * 100), 1)

        print("Position APR: \x1b[31m{} %\x1b[0m".format(apr))
        print("Flare amount: \x1b[32m{}\x1b[0m\n\n".format(Web3.fromWei(web3.eth.getBalance(account.address), 'ether')))

        # Check if we need to compound
        if rewards > compound_above:
            print("\x1b[32mCompunding Rewards\x1b[0m")
            compound(web3, account)

        # Cycle through every minute and have a peek
        time.sleep(60)
