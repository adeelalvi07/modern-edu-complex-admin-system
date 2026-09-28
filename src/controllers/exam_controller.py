"""
Academic Examination & Statistical Analytics Controller.
Calculates Mean, Variance, Standard Deviation, and Gaussian Pass/Fail Probabilities.
"""
import math
from typing import List, Dict, Any, Optional
import numpy as np
from config import settings

def calculate_grade(percentage: float) -> str:
    """Assigns letter grade based on school's grading configuration."""
    for item in settings.DEFAULT_GRADING:
        if percentage >= item["min"]:
            return item["grade"]
    return "F"

def get_standard_curriculum_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Returns recommended standard subjects and marks based on class grade level."""
    cn = (class_name or "").strip().lower()
    if any(k in cn for k in ["playgroup", "nursery", "prep", "pg", "kindergarten", "kg"]):
        return [
            {"name": "English", "code": "ENG", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Urdu", "code": "URD", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Mathematics", "code": "MAT", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "General Knowledge & Art", "code": "GKA", "total_marks": 100.0, "passing_marks": 40.0},
        ]
    elif any(k in cn for k in ["class 1", "class 2", "class 3", "class 4", "class 5"]):
        return [
            {"name": "English", "code": "ENG", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Urdu", "code": "URD", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Mathematics", "code": "MAT", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "General Science", "code": "SCI", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Islamiat", "code": "ISL", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Social Studies", "code": "SST", "total_marks": 100.0, "passing_marks": 40.0},
        ]
    elif any(k in cn for k in ["class 6", "class 7", "class 8"]):
        return [
            {"name": "English", "code": "ENG", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Urdu", "code": "URD", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Mathematics", "code": "MAT", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "General Science", "code": "SCI", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Computer Science", "code": "CS", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Islamiat", "code": "ISL", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "History & Geography", "code": "HG", "total_marks": 100.0, "passing_marks": 40.0},
        ]
    else:
        # Class 9, Class 10 (Matriculation)
        return [
            {"name": "English", "code": "ENG", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Urdu", "code": "URD", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Mathematics", "code": "MAT", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Physics", "code": "PHY", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Chemistry", "code": "CHM", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Biology / Computer", "code": "BIO", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Islamiat", "code": "ISL", "total_marks": 100.0, "passing_marks": 40.0},
            {"name": "Pakistan Studies", "code": "PKS", "total_marks": 100.0, "passing_marks": 40.0},
        ]

class ExamController:
    """Provides statistical calculations and marks validation."""

    @staticmethod
    def compute_class_statistics(scores: List[float], passing_mark: float = 40.0) -> Dict[str, Any]:
        """
        Computes comprehensive descriptive and inferential statistics for a class test/exam.
        Returns:
            - count: int
            - mean: float
            - median: float
            - variance: float
            - std_dev: float
            - min_score: float
            - max_score: float
            - pass_count: int
            - fail_count: int
            - pass_percentage: float
            - pass_probability: float (Estimated based on normal distribution)
        """
        if not scores:
            return {
                "count": 0, "mean": 0.0, "median": 0.0, "variance": 0.0,
                "std_dev": 0.0, "min_score": 0.0, "max_score": 0.0,
                "pass_count": 0, "fail_count": 0, "pass_percentage": 0.0,
                "pass_probability": 0.0
            }

        arr = np.array(scores, dtype=float)
        count = int(len(arr))
        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))
        var_val = float(np.var(arr, ddof=1)) if count > 1 else 0.0
        std_val = float(np.std(arr, ddof=1)) if count > 1 else 0.0
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))

        pass_count = int(np.sum(arr >= passing_mark))
        fail_count = count - pass_count
        pass_pct = round((pass_count / count) * 100, 1)

        # Inferential Statistics: Pass probability modeled as 1 - CDF(passing_mark)
        # Using cumulative standard normal distribution
        if std_val > 0.0:
            z_score = (passing_mark - mean_val) / std_val
            # Normal distribution CDF approximation via error function (erf)
            # P(X >= passing_mark) = 1 - 0.5 * (1 + erf(z / sqrt(2)))
            pass_prob = 1.0 - 0.5 * (1.0 + math.erf(z_score / math.sqrt(2.0)))
            pass_prob_pct = round(max(0.0, min(1.0, pass_prob)) * 100.0, 1)
        else:
            pass_prob_pct = 100.0 if mean_val >= passing_mark else 0.0

        return {
            "count": count,
            "mean": round(mean_val, 2),
            "median": round(median_val, 2),
            "variance": round(var_val, 2),
            "std_dev": round(std_val, 2),
            "min_score": round(min_val, 2),
            "max_score": round(max_val, 2),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_percentage": pass_pct,
            "pass_probability": pass_prob_pct
        }
