from __future__ import annotations

from app.blockchain.chain_ids import is_wallet_scan_supported
from app.collectors.etherscan_client import EtherscanClient
from app.core.exceptions import AlphaHunterError
from app.core.logging import get_logger
from app.models.token import Token
from app.models.whale_event import WhaleEvent
from app.repositories.wallet_holding_repository import WalletHoldingRepository
from app.repositories.wallet_repository import WalletRepository
from app.repositories.whale_event_repository import WhaleEventRepository
from app.wallets.classification import classify_holder
from app.wallets.holder_aggregator import aggregate_net_balances, rank_top_holders
from app.wallets.whale_detection import classify_balance_change

log = get_logger(__name__)


class UnsupportedChainForWalletScan(AlphaHunterError):
    error_code = "UNSUPPORTED_CHAIN_FOR_WALLET_SCAN"
    recoverable = False


class WalletDiscoveryService:
    """Scans a token's recent transfer history and records approximate
    top holders, detecting whale events (new positions, increases,
    decreases) on each scan.

    NOT wired to the scheduler -- each scan is an external API call
    against a bounded transfer window, and running this automatically
    for every token on every ingestion cycle would burn through free-tier
    rate limits fast.
    """

    def __init__(
        self,
        client: EtherscanClient,
        wallet_repository: WalletRepository,
        holding_repository: WalletHoldingRepository,
        whale_event_repository: WhaleEventRepository,
    ) -> None:
        self._client = client
        self._wallet_repo = wallet_repository
        self._holding_repo = holding_repository
        self._whale_event_repo = whale_event_repository

    async def scan_token(self, token: Token, top_n: int = 20) -> int:
        if not is_wallet_scan_supported(token.chain):
            raise UnsupportedChainForWalletScan(
                f"Wallet scanning not supported for chain '{token.chain.value}' yet",
                details={"chain": token.chain.value},
            )

        transfers = await self._client.get_recent_transfers(token.chain, token.contract_address)
        balances = aggregate_net_balances(transfers)
        top_holders = rank_top_holders(balances, top_n=top_n)

        for address, balance, rank in top_holders:
            wallet_type, confidence = classify_holder(rank, len(top_holders))
            wallet = await self._wallet_repo.get_or_create(token.chain, address, wallet_type, confidence)
            holding, previous_balance = await self._holding_repo.upsert(token.id, wallet.id, balance, rank)

            detection = classify_balance_change(previous_balance, balance, token.price_usd)
            if detection is not None:
                self._whale_event_repo.session.add(
                    WhaleEvent(
                        token_id=token.id, wallet_id=wallet.id, event_type=detection.event_type,
                        previous_balance=previous_balance, new_balance=balance,
                        change_pct=detection.change_pct, change_usd=detection.change_usd,
                    )
                )

        log.info(
            "wallet_scan_complete", token_id=str(token.id), symbol=token.symbol,
            transfers_analyzed=len(transfers), holders_found=len(top_holders),
        )
        return len(top_holders)