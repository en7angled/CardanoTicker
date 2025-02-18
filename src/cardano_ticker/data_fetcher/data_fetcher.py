import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta

from blockfrost import ApiError, ApiUrls, BlockFrostApi

from cardano_ticker.data_fetcher.crypto_price_fetcher import CryptoPriceFetcher

logging.basicConfig(level=logging.INFO)


class DataFetcher:
    def __init__(self, api_key="", blockfrost_project_id=""):
        blockfrost_id = os.getenv("BLOCKFROST_PROJECT_ID", default=blockfrost_project_id)

        self.blockfrost_api = BlockFrostApi(
            project_id=blockfrost_id,
            base_url=ApiUrls.mainnet.value,
        )

        self.price_fetcher = CryptoPriceFetcher(api_key)
        self.cached_stats = None

    def get_chart_data(self, symbol, currency, days=7):
        return self.price_fetcher.get_chart_data(symbol, currency, days)

    def get_realtime(self, symbol, currency):
        return self.price_fetcher.get_realtime(symbol, currency)

    def pool(self, pool_id):
        return self.blockfrost_api.pool(pool_id, return_type="json")

    def pool_history(self, pool_id):
        return self.blockfrost_api.pool_history(pool_id, return_type="json")

    def pool_name_and_ticker(self, pool_id):
        pool_data = self.blockfrost_api.pool_metadata(pool_id, return_type="json")
        return pool_data["name"], pool_data["ticker"]

    def network(self):
        return self.blockfrost_api.network(return_type="json")

    def cardano_transactions_data(self):
        try:
            # Get the latest block
            latest_block = self.blockfrost_api.block_latest(return_type="json")
            latest_time = datetime.fromtimestamp(latest_block["time"])

            # Initialize variables
            transactions_per_min = defaultdict(int)
            current_block = latest_block["hash"]

            # Traverse blocks to gather data for the past 30 minutes
            idx = 0
            while True:
                idx += 1
                block_data = self.blockfrost_api.block(current_block, return_type="json")
                block_time = datetime.fromtimestamp(block_data["time"])

                # Get the minute of the block
                minute = block_time.strftime("%Y-%m-%d %H:%M")

                # Accumulate transactions for each day
                transactions_per_min[minute] += block_data["tx_count"]

                # Break if we exceed 30 minutes
                if block_time < latest_time - timedelta(minutes=30):
                    break

                # Move to the previous block
                current_block = block_data["previous_block"]

            # Ensure data is sorted by date
            transactions_per_min = dict(sorted(transactions_per_min.items()))
            return {
                "dates": list(transactions_per_min.keys()),
                "transactions": list(transactions_per_min.values()),
            }

        except ApiError as e:
            print(f"Blockfrost API error: {e}")
            return {"dates": [], "transactions": []}

    def blockchain_stats(self):
        try:
            current_time = datetime.now().timestamp()  # Current UNIX timestamp

            if self.cached_stats is not None:
                last_time, stats = self.cached_stats
                # If the data is less than 30 minute old, return the cached data
                if current_time - last_time < 29 * 60:
                    return stats

            api = self.blockfrost_api
            # Fetch current epoch
            current_epoch = api.epoch_latest(return_type="json")
            epoch_number = current_epoch["epoch"]

            epoch_start_time = current_epoch["start_time"]  # UNIX timestamp
            epoch_end_time = current_epoch["end_time"]  # UNIX timestamp
            # Calculate progress percentage
            total_epoch_duration = epoch_end_time - epoch_start_time
            elapsed_time = current_time - epoch_start_time
            percentage_progress = (elapsed_time / total_epoch_duration) * 100

            remaining_seconds = epoch_end_time - current_time
            remaining_time = str(timedelta(seconds=int(remaining_seconds)))

            # Fetch active stake and convert to billions ADA
            active_stake = round(int(current_epoch["active_stake"]) / 1e15, 2)

            # Fetch total stake pools
            stake_pools = api.pools(gather_pages=True)
            total_stake_pools = len(stake_pools)

            transaction_data = self.cardano_transactions_data()

            stats = {
                "epoch_number": epoch_number,
                "remaining_time": remaining_time,
                "percentage_progress": percentage_progress,
                "active_stake": active_stake,
                "total_stake_pools": total_stake_pools,
                "transactions": transaction_data,
            }

            self.cached_stats = (current_time, stats)
            return stats
        except ApiError as e:
            print(f"Blockfrost API error: {e}")
            return None
