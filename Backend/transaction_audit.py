"""Admin-only transaction history search and Sepolia verification."""
from datetime import datetime, timezone
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from models import BlockchainTransactionAudit
from admin_auth import require_admin_api

router = APIRouter(prefix="/admin/api/transaction-audit", tags=["Transaction Audit"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _serialise(row):
    return {
        "transaction_number": row.transaction_number,
        "tx_hash": row.tx_hash,
        "chain_id": row.chain_id,
        "network_name": row.network_name,
        "contract_address": row.contract_address,
        "operation_type": row.operation_type,
        "block_number": row.block_number,
        "transaction_status": row.transaction_status,
        "gas_used": row.gas_used,
        "created_at": row.created_at,
        "verified_at": row.verified_at,
        "last_verification_status": row.last_verification_status,
        "last_verification_details": row.last_verification_details,
        "explorer_url": f"https://sepolia.etherscan.io/tx/{row.tx_hash}" if row.chain_id == 11155111 else None,
    }


@router.get("/search")
def search_transactions(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    _admin: dict = Depends(require_admin_api),
    db: Session = Depends(get_db),
):
    """Search by internal transaction number, hash, or operation name."""
    query = db.query(BlockchainTransactionAudit)
    q = q.strip()
    if q:
        escaped = q.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(
            BlockchainTransactionAudit.transaction_number.ilike(f"%{escaped}%") |
            BlockchainTransactionAudit.tx_hash.ilike(f"%{escaped}%") |
            BlockchainTransactionAudit.operation_type.ilike(f"%{escaped}%")
        )
    rows = query.order_by(BlockchainTransactionAudit.id.desc()).limit(limit).all()
    return {"count": len(rows), "transactions": [_serialise(row) for row in rows]}


@router.get("/{identifier}/verify")
def verify_transaction(
    identifier: str,
    _admin: dict = Depends(require_admin_api),
    db: Session = Depends(get_db),
):
    """Verify a saved transaction or directly verify a full transaction hash."""
    from blockchain import web3, CONTRACT_ADDRESS

    identifier = identifier.strip()
    row = db.query(BlockchainTransactionAudit).filter(
        (BlockchainTransactionAudit.transaction_number == identifier) |
        (BlockchainTransactionAudit.tx_hash == identifier)
    ).first()
    tx_hash = row.tx_hash if row else identifier

    if not re.fullmatch(r"0x[a-fA-F0-9]{64}", tx_hash):
        raise HTTPException(
            status_code=404 if row is None else 400,
            detail="No audit record found for that transaction number. For older records not in this table, search using the full 0x transaction hash.",
        )

    try:
        tx = web3.eth.get_transaction(tx_hash)
        receipt = web3.eth.get_transaction_receipt(tx_hash)
        block = web3.eth.get_block(receipt["blockNumber"])
        actual_chain_id = int(web3.eth.chain_id)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Blockchain RPC could not verify the transaction ({type(exc).__name__}). This is not proof that the transaction failed.",
        ) from exc

    actual_to = tx.get("to")
    receipt_status = int(receipt.get("status", 0))
    actual_status = "confirmed" if receipt_status == 1 else "failed"
    checks = {
        "transaction_found": True,
        "receipt_found": receipt is not None,
        "successful_execution": receipt_status == 1,
        "sepolia_network": actual_chain_id == 11155111,
        "expected_contract": bool(actual_to) and actual_to.lower() == str(CONTRACT_ADDRESS).lower(),
        "database_record_found": row is not None,
        "database_hash_matches": bool(row) and row.tx_hash.lower() == tx_hash.lower(),
        "database_chain_matches": bool(row) and row.chain_id == actual_chain_id,
        "database_contract_matches": bool(row) and row.contract_address.lower() == str(actual_to or "").lower(),
        "database_block_matches": bool(row) and row.block_number == int(receipt["blockNumber"]),
        "database_status_matches": bool(row) and row.transaction_status == actual_status,
    }

    if receipt_status != 1:
        overall = "ON_CHAIN_FAILED"
    elif not checks["sepolia_network"] or not checks["expected_contract"]:
        overall = "NETWORK_OR_CONTRACT_MISMATCH"
    elif row is None:
        overall = "ON_CHAIN_FOUND_NO_DATABASE_AUDIT_RECORD"
    elif all(checks.values()):
        overall = "VERIFIED_MATCH"
    else:
        overall = "DATABASE_BLOCKCHAIN_MISMATCH"

    verified_at = _now()
    result = {
        "overall_status": overall,
        "checks": checks,
        "blockchain": {
            "chain_id": actual_chain_id,
            "tx_hash": tx_hash,
            "from": tx.get("from"),
            "to": actual_to,
            "block_number": int(receipt["blockNumber"]),
            "block_timestamp": datetime.fromtimestamp(int(block["timestamp"]), timezone.utc).isoformat(),
            "receipt_status": receipt_status,
            "gas_used": int(receipt.get("gasUsed", 0)),
            "configured_contract_address": str(CONTRACT_ADDRESS),
            "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hash}" if actual_chain_id == 11155111 else None,
        },
        "database": _serialise(row) if row else None,
        "verified_at": verified_at,
    }
    if row:
        row.verified_at = verified_at
        row.last_verification_status = overall
        row.last_verification_details = str(checks)
        db.commit()
    return result
