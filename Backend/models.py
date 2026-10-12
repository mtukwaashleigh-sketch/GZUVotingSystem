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

    # A student can vote once for each position,
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
