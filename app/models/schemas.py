from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ==============================================================================
# Overview Schemas
# ==============================================================================

class SystemCoverage(BaseModel):
    system_id: int
    system_name: str
    min_year: int
    max_year: int
    total_institutions: int
    total_criteria: int

class CountryCount(BaseModel):
    country_id: int
    country_name: str
    university_count: int

class MultiSystemUniversity(BaseModel):
    university_id: int
    university_name: str
    country_name: str
    system_count: int
    systems: List[str]

class OverviewKPIs(BaseModel):
    total_universities: int
    total_countries: int
    total_ranking_systems: int
    total_ranking_records: int
    total_demographic_records: int
    min_year: int
    max_year: int
    ranking_systems: List[SystemCoverage]
    top_countries: List[CountryCount]
    universities_in_all_systems: int
    universities_in_multiple_systems: int

# ==============================================================================
# Comparison Schemas
# ==============================================================================

class CriterionScorePoint(BaseModel):
    criteria_id: int
    criteria_name: str
    metric_type: str  # 'score' or 'rank'
    year: int
    value: Optional[float]

class UniversityDemographicPoint(BaseModel):
    year: int
    num_students: Optional[int]
    student_staff_ratio: Optional[float]
    pct_international_students: Optional[int]
    pct_female_students: Optional[float]

class UniversityComparisonItem(BaseModel):
    university_id: int
    university_name: str
    country_name: str
    scores: List[CriterionScorePoint]
    demographics: List[UniversityDemographicPoint]

class UniversityComparisonResponse(BaseModel):
    system_id: int
    system_name: str
    universities: List[UniversityComparisonItem]
    warnings: List[str] = Field(default_factory=list)

# ==============================================================================
# Country Schemas
# ==============================================================================

class CountryRepresentation(BaseModel):
    system_id: int
    system_name: str
    university_count: int

class CountryScoreMetric(BaseModel):
    criteria_id: int
    criteria_name: str
    metric_type: str
    year: int
    count: int
    mean: float
    min: float
    max: float
    median: float

class CountryDetailResponse(BaseModel):
    country_id: int
    country_name: str
    total_universities: int
    system_representation: List[CountryRepresentation]
    score_metrics: List[CountryScoreMetric]

# ==============================================================================
# Trends Schemas
# ==============================================================================

class TrendDataPoint(BaseModel):
    year: int
    score: Optional[float]
    rank_in_system: Optional[int]

class UniversityTrendSeries(BaseModel):
    university_id: int
    university_name: str
    criteria_id: int
    criteria_name: str
    metric_type: str
    data_points: List[TrendDataPoint]

class TopMover(BaseModel):
    university_id: int
    university_name: str
    country_name: str
    start_year: int
    end_year: int
    start_score: float
    end_score: float
    absolute_change: float
    percent_change: float

class TrendsResponse(BaseModel):
    system_id: int
    system_name: str
    criteria_id: int
    criteria_name: str
    metric_type: str
    trends: List[UniversityTrendSeries]
    strongest_improvements: List[TopMover] = Field(default_factory=list)
    strongest_declines: List[TopMover] = Field(default_factory=list)

# ==============================================================================
# Criteria Analysis Schemas
# ==============================================================================

class CriteriaCorrelation(BaseModel):
    criteria_1_id: int
    criteria_1_name: str
    criteria_2_id: int
    criteria_2_name: str
    system_id: int
    system_name: str
    year: Optional[int]
    sample_size: int
    pearson_r: float
    interpretation: str

class CriteriaDistribution(BaseModel):
    criteria_id: int
    criteria_name: str
    system_id: int
    system_name: str
    metric_type: str
    count: int
    mean: float
    std_dev: float
    min: float
    q25: float
    median: float
    q75: float
    max: float

class CriteriaAnalysisResponse(BaseModel):
    distributions: List[CriteriaDistribution]
    correlations: List[CriteriaCorrelation]
    notes: List[str] = Field(default_factory=list)

# ==============================================================================
# Demographics Schemas
# ==============================================================================

class DemographicDistribution(BaseModel):
    metric_name: str
    count: int
    mean: float
    min: float
    median: float
    max: float
    unit: str

class DemographicCorrelation(BaseModel):
    demographic_field: str
    criteria_id: int
    criteria_name: str
    sample_size: int
    pearson_r: float
    interpretation: str

class DemographicsResponse(BaseModel):
    total_observations: int
    unique_universities: int
    years_covered: List[int]
    distributions: List[DemographicDistribution]
    correlations: List[DemographicCorrelation]
    methodology_note: str
