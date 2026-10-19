from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint, text

from database import Base


class Voter(Base):

    __tablename__ = "voters"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    student_id = Column(
        String,
        unique=True,
        index=True
    )

    email = Column(
        String,
        unique=True,
        index=True
    )

    password = Column(
        String
    )
    full_name = Column(String, nullable=True)
    identity_type = Column(String, nullable=False, default="student")


class InstitutionalIdentity(Base):
    """Authoritative student and employee identity roster supplied by GZU HR/Registry."""
    __tablename__ = "institutional_identities"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, nullable=False, unique=True, index=True)
    full_name = Column(String, nullable=False)
    identity_type = Column(String, nullable=False)  # student or employee
    institutional_email = Column(String, nullable=True)


class Election(Base):

    __tablename__ = "elections"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String,
        nullable=False
    )

    description = Column(
        String
    )

    # JSON-encoded list of positions open for nominations in this election.
    open_positions = Column(String, nullable=False, default="[]", server_default="[]")

    status = Column(
        String,
        default="upcoming"
    )
    blockchain_election_id = Column(
        Integer,
        nullable=True,
        unique=True
    )

    # Soft deletion preserves the election row and its blockchain ID/history.
    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false")
    )


class Candidate(Base):

    __tablename__ = "candidates"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    election_id = Column(
        Integer,
        nullable=False
    )

    name = Column(
        String,
        nullable=False
    )

    position = Column(
        String,
        nullable=False
    )

    blockchain_candidate_id = Column(
        Integer,
        nullable=True
    )

    # Soft withdrawal: keep the database row and blockchain mapping/history.
    is_withdrawn = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false")
    )


class VotingRecord(Base):

    __tablename__ = "voting_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    student_id = Column(
        String,
        nullable=False
    )

    election_id = Column(
        Integer,
        nullable=False
    )

    position = Column(
        String,
        nullable=False
    )

    # An eligible voter can vote once for each position,
    # but cannot vote twice for the same position.
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "election_id",
            "position",
            name="unique_student_election_position_vote"
        ),
    )


class Vote(Base):

    __tablename__ = "votes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    election_id = Column(
        Integer,
        nullable=False
    )

    candidate_id = Column(
        Integer,
        nullable=False
    )

class CandidateNomination(Base):
    __tablename__ = "candidate_nominations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, nullable=False, index=True)
    election_id = Column(Integer, nullable=False, index=True)
    position = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    department = Column(String, nullable=False)
    programme = Column(String, nullable=False)
    year_of_study = Column(String, nullable=False)
    manifesto = Column(String, nullable=False)
    experience = Column(String, nullable=False, default="")
    photo_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    admin_feedback = Column(String, nullable=True)
    candidate_id = Column(Integer, nullable=True)
    created_at = Column(String, nullable=False)
    reviewed_at = Column(String, nullable=True)
    identity_mapping_hash = Column(String, nullable=True, index=True)


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, unique=True, index=True)
    photo_path = Column(String, nullable=True)
    faculty = Column(String, nullable=True)
    department = Column(String, nullable=True)
    programme = Column(String, nullable=True)
    year_of_study = Column(String, nullable=True)
    manifesto = Column(String, nullable=True)
    experience = Column(String, nullable=True)


class VoterReceipt(Base):
    """Receipt lookup record without plaintext voter identity or candidate choice."""
    __tablename__ = "voter_receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_hash = Column(String(64), nullable=False, unique=True, index=True)
    election_id = Column(Integer, nullable=False, index=True)
    chain_id = Column(Integer, nullable=False, index=True)
    # JSON array of transaction hashes; kept server-side and never returned by verify endpoint.
    transaction_hashes = Column(String, nullable=False)
    expected_transactions = Column(Integer, nullable=False)
    created_at = Column(String(40), nullable=False, index=True)
    # Institutional identifier of the authenticated voter; nullable for legacy receipts.
    owner_identifier = Column(String(120), nullable=True, index=True)


class BlockchainTransactionAudit(Base):
    """Durable searchable record of a transaction submitted by the application."""
    __tablename__ = "blockchain_transaction_audit"

    id = Column(Integer, primary_key=True, index=True)
    transaction_number = Column(String(40), nullable=False, unique=True, index=True)
    tx_hash = Column(String(80), nullable=False, unique=True, index=True)
    chain_id = Column(Integer, nullable=False, index=True)
    network_name = Column(String(40), nullable=False, default="Sepolia")
    contract_address = Column(String(80), nullable=False, index=True)
    operation_type = Column(String(100), nullable=False, index=True)
    block_number = Column(Integer, nullable=True, index=True)
    transaction_status = Column(String(30), nullable=False, index=True)
    gas_used = Column(String(40), nullable=True)
    created_at = Column(String(40), nullable=False, index=True)
    verified_at = Column(String(40), nullable=True)
    last_verification_status = Column(String(40), nullable=True)
    last_verification_details = Column(String, nullable=True)


class VoterAccountVerification(Base):
    """Short-lived email verification challenges; no plaintext OTP is stored."""
    __tablename__ = "voter_account_verifications"
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False)
    code_hash = Column(String, nullable=False)
    expires_at = Column(Integer, nullable=False)
    last_sent_at = Column(Integer, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
