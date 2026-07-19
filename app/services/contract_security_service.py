from __future__ import annotations

from app.blockchain.chain_ids import is_evm_chain
from app.collectors.goplus_client import GoPlusClient
from app.contracts.risk_scoring import compute_contract_risk
from app.core.exceptions import AlphaHunterError
from app.core.logging import get_logger
from app.models.token import Token
from app.repositories.contract_security_repository import ContractSecurityRepository

log = get_logger(__name__)


class UnsupportedChainForSecurityScan(AlphaHunterError):
    error_code = "UNSUPPORTED_CHAIN_FOR_SECURITY_SCAN"
    recoverable = False


class ContractSecurityService:
    """On-demand, like WalletDiscoveryService (M11) -- not scheduled
    automatically. GoPlus's free tier is generous but not unlimited;
    running this for every token on every ingestion cycle isn't
    warranted before there's a real usage pattern to size it against."""

    def __init__(self, client: GoPlusClient, repository: ContractSecurityRepository) -> None:
        self._client = client
        self._repository = repository

    async def scan_token(self, token: Token) -> int:
        if not is_evm_chain(token.chain):
            raise UnsupportedChainForSecurityScan(
                f"Contract security scanning not supported for chain '{token.chain.value}' yet",
                details={"chain": token.chain.value},
            )

        security = await self._client.get_token_security(token.chain, token.contract_address)
        risk = compute_contract_risk(security)
        await self._repository.upsert(token.id, risk)

        log.info(
            "contract_security_scan_complete",
            token_id=str(token.id),
            symbol=token.symbol,
            safety_score=risk.safety_score,
            is_honeypot=risk.is_honeypot,
        )
        return risk.safety_score
