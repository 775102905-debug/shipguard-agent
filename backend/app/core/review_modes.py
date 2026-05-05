from dataclasses import dataclass
from typing import Dict, Optional

from ..schemas.review import ReviewMode


@dataclass
class ReviewModeProfile:
    label: str
    pass_threshold: int
    conditional_threshold: int

    security_multiplier: float = 1.0
    documentation_multiplier: float = 1.0
    dependency_multiplier: float = 1.0
    deployment_multiplier: float = 1.0
    testing_multiplier: float = 1.0
    maintainability_multiplier: float = 1.0

    penalty_missing_readme: int = 4
    penalty_missing_env_example: int = 4
    penalty_missing_gitignore: int = 4
    penalty_missing_tests: int = 3
    penalty_missing_license: int = 2

    security_high_penalty: int = 8
    security_med_penalty: int = 4
    security_low_penalty: int = 2

    dependency_high_penalty: int = 5
    dependency_med_penalty: int = 3

    max_high_security_for_conditional_pass: Optional[int] = None
    max_high_security_for_pass: Optional[int] = None

    guidance: str = ""


STUDENT = ReviewModeProfile(
    label="学生作业",
    pass_threshold=65,
    conditional_threshold=50,
    security_multiplier=0.9,
    documentation_multiplier=0.8,
    dependency_multiplier=0.8,
    deployment_multiplier=0.5,
    testing_multiplier=0.6,
    maintainability_multiplier=0.8,
    penalty_missing_tests=2,
    penalty_missing_license=1,
    security_high_penalty=7,
    security_med_penalty=3,
    security_low_penalty=1,
    max_high_security_for_pass=1,
    guidance=(
        "学生作业模式重点关注核心功能是否完成、README 是否能说明基本运行方式。"
        "对 LICENSE、Docker 部署、完整测试和依赖精确锁版本相对宽容。"
        "如有高危安全问题会严格扣分。"
    ),
)

GITHUB = ReviewModeProfile(
    label="GitHub 展示项目",
    pass_threshold=75,
    conditional_threshold=60,
    security_multiplier=1.0,
    documentation_multiplier=1.2,
    dependency_multiplier=1.0,
    deployment_multiplier=1.0,
    testing_multiplier=0.8,
    maintainability_multiplier=1.0,
    penalty_missing_readme=5,
    penalty_missing_env_example=4,
    penalty_missing_tests=2,
    penalty_missing_license=3,
    guidance=(
        "GitHub 展示模式重点关注陌生开发者能否快速理解、克隆和运行项目。"
        "README 完整性、LICENSE、快速启动说明和 .env.example 更加重要。"
        "安全问题会影响项目可信度。"
    ),
)

INTERVIEW = ReviewModeProfile(
    label="面试项目",
    pass_threshold=75,
    conditional_threshold=60,
    security_multiplier=1.1,
    documentation_multiplier=1.0,
    dependency_multiplier=1.2,
    deployment_multiplier=0.9,
    testing_multiplier=1.5,
    maintainability_multiplier=1.3,
    penalty_missing_tests=4,
    penalty_missing_license=2,
    security_high_penalty=9,
    security_med_penalty=4,
    dependency_high_penalty=6,
    dependency_med_penalty=4,
    guidance=(
        "面试项目模式重点关注候选人的工程素养：测试覆盖、依赖管理、"
        "项目结构清晰度和架构表达能力。测试缺失和依赖未锁版本会明显扣分。"
    ),
)

COMMERCIAL = ReviewModeProfile(
    label="商业交付",
    pass_threshold=82,
    conditional_threshold=68,
    security_multiplier=1.3,
    documentation_multiplier=1.1,
    dependency_multiplier=1.2,
    deployment_multiplier=1.5,
    testing_multiplier=1.2,
    maintainability_multiplier=1.1,
    penalty_missing_readme=5,
    penalty_missing_env_example=5,
    penalty_missing_gitignore=4,
    penalty_missing_tests=4,
    penalty_missing_license=3,
    security_high_penalty=10,
    security_med_penalty=5,
    security_low_penalty=3,
    max_high_security_for_conditional_pass=1,
    max_high_security_for_pass=0,
    guidance=(
        "商业交付模式是最严格的审查模式。重点关注安全隔离、配置管理、"
        "部署材料完备性、依赖锁定、测试覆盖和后续可维护性。"
        "安全类问题扣分更重。存在高危安全问题时不能获得 PASS 结论。"
    ),
)


MODE_PROFILES: Dict[ReviewMode, ReviewModeProfile] = {
    ReviewMode.student_assignment: STUDENT,
    ReviewMode.github_showcase: GITHUB,
    ReviewMode.interview_project: INTERVIEW,
    ReviewMode.commercial_delivery: COMMERCIAL,
}


def get_profile(mode: ReviewMode) -> ReviewModeProfile:
    return MODE_PROFILES.get(mode, STUDENT)
