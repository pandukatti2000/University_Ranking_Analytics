from sqlalchemy import Column, Integer, SmallInteger, String, Numeric, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.session import Base

class Country(Base):
    __tablename__ = "country"

    id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String(100), nullable=False, unique=True, index=True)

    universities = relationship("University", back_populates="country")

    def __repr__(self):
        return f"<Country(id={self.id}, name='{self.country_name}')>"


class RankingSystem(Base):
    __tablename__ = "ranking_system"

    id = Column(Integer, primary_key=True, index=True)
    system_name = Column(String(100), nullable=False, unique=True)

    criteria = relationship("RankingCriteria", back_populates="ranking_system")

    def __repr__(self):
        return f"<RankingSystem(id={self.id}, name='{self.system_name}')>"


class RankingCriteria(Base):
    __tablename__ = "ranking_criteria"

    id = Column(Integer, primary_key=True, index=True)
    ranking_system_id = Column(Integer, ForeignKey("ranking_system.id", ondelete="RESTRICT"), nullable=False, index=True)
    criteria_name = Column(String(200), nullable=False)

    __table_args__ = (
        UniqueConstraint("ranking_system_id", "criteria_name", name="uq_sys_crit"),
    )

    ranking_system = relationship("RankingSystem", back_populates="criteria")
    rankings = relationship("UniversityRankingYear", back_populates="ranking_criteria")

    @property
    def is_rank(self) -> bool:
        """Returns True if this criterion represents an ordinal rank (1=best, lower is better)."""
        return 14 <= self.id <= 20

    @property
    def metric_type(self) -> str:
        return "rank" if self.is_rank else "score"

    def __repr__(self):
        return f"<RankingCriteria(id={self.id}, system_id={self.ranking_system_id}, name='{self.criteria_name}')>"


class University(Base):
    __tablename__ = "university"

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("country.id", ondelete="RESTRICT"), nullable=False, index=True)
    university_name = Column(String(200), nullable=False, index=True)

    country = relationship("Country", back_populates="universities")
    rankings = relationship("UniversityRankingYear", back_populates="university")
    demographics = relationship("UniversityYear", back_populates="university")

    def __repr__(self):
        return f"<University(id={self.id}, name='{self.university_name}', country_id={self.country_id})>"


class UniversityRankingYear(Base):
    __tablename__ = "university_ranking_year"

    university_id = Column(Integer, ForeignKey("university.id", ondelete="CASCADE"), primary_key=True)
    ranking_criteria_id = Column(Integer, ForeignKey("ranking_criteria.id", ondelete="CASCADE"), primary_key=True)
    year = Column(SmallInteger, primary_key=True)
    score = Column(Numeric(6, 2), nullable=True)

    __table_args__ = (
        CheckConstraint("year BETWEEN 2000 AND 2030", name="chk_ury_year"),
    )

    university = relationship("University", back_populates="rankings")
    ranking_criteria = relationship("RankingCriteria", back_populates="rankings")

    def __repr__(self):
        return f"<UniversityRankingYear(uni={self.university_id}, crit={self.ranking_criteria_id}, year={self.year}, score={self.score})>"


class UniversityYear(Base):
    __tablename__ = "university_year"

    university_id = Column(Integer, ForeignKey("university.id", ondelete="CASCADE"), primary_key=True)
    year = Column(SmallInteger, primary_key=True)
    num_students = Column(Integer, nullable=False)
    student_staff_ratio = Column(Numeric(5, 2), nullable=False)
    pct_international_students = Column(SmallInteger, nullable=False)
    pct_female_students = Column(Numeric(5, 2), nullable=True)

    __table_args__ = (
        CheckConstraint("year BETWEEN 2000 AND 2030", name="chk_uy_year"),
        CheckConstraint("num_students > 0", name="chk_uy_students"),
        CheckConstraint("student_staff_ratio > 0", name="chk_uy_ratio"),
        CheckConstraint("pct_international_students BETWEEN 0 AND 100", name="chk_uy_intl"),
        CheckConstraint("pct_female_students BETWEEN 0 AND 100", name="chk_uy_female"),
    )

    university = relationship("University", back_populates="demographics")

    def __repr__(self):
        return f"<UniversityYear(uni={self.university_id}, year={self.year}, students={self.num_students})>"
