# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Service for database-driven non-work item types (e.g. Management Plan)."""
from submit_api.enums.non_work_item import NonWorkItemEligibility, NonWorkItemType
from submit_api.exceptions import ResourceNotFoundError
from submit_api.models.non_work_item_type_config import NonWorkItemTypeConfig
from submit_api.models.project import Project


class NonWorkItemTypeService:
    """Resolve which non-work item types apply to a project."""

    @classmethod
    def get_eligible_for_project(cls, project: Project, onboarding_only: bool = False) -> list:
        """Return the active non-work item types the project is eligible for, in display order.

        When onboarding_only is True, only types offered as onboarding selections are returned.
        """
        if not project:
            return []
        configs = NonWorkItemTypeConfig.get_all_active()
        if onboarding_only:
            configs = [config for config in configs if config.is_onboarding_option]
        return [config for config in configs if cls._is_eligible(project, config)]

    @classmethod
    def get_eligible_for_project_id(cls, project_id: int) -> list:
        """Return the eligible non-work item types for a project id."""
        project = Project.find_by_id(project_id)
        if not project:
            raise ResourceNotFoundError(f"Project {project_id} not found.")
        return cls.get_eligible_for_project(project)

    @classmethod
    def is_eligible(cls, project: Project, item_type: NonWorkItemType, onboarding_only: bool = False) -> bool:
        """Return True if the project is eligible for the given non-work item type.

        When onboarding_only is True, types that are not onboarding options are never eligible.
        """
        config = NonWorkItemTypeConfig.find_by_code(item_type.value)
        if not config or not project:
            return False
        if onboarding_only and not config.is_onboarding_option:
            return False
        return cls._is_eligible(project, config)

    @staticmethod
    def _is_eligible(project: Project, config: NonWorkItemTypeConfig) -> bool:
        """Apply the config's eligibility rule to the project."""
        rule = config.eligibility_rule
        if rule == NonWorkItemEligibility.ALWAYS:
            return True
        if rule == NonWorkItemEligibility.APPROVED_CONDITION:
            return bool(project.has_approved_condition)
        return False
