from typing import List, Optional, Union
from posthog.hogql.constants import LimitContext
from posthog.hogql.timings import HogQLTimings
from posthog.hogql_queries.insights.query_context import QueryContext
from posthog.models.filters.mixins.utils import cached_property
from posthog.models.property.util import box_value
from posthog.models.team.team import Team
from posthog.schema import (
    BreakdownAttributionType,
    BreakdownFilter,
    BreakdownType,
    FunnelConversionWindowTimeUnit,
    FunnelsActorsQuery,
    FunnelsFilter,
    FunnelsQuery,
    HogQLQueryModifiers,
    IntervalType,
)


class FunnelQueryContext(QueryContext):
    query: FunnelsQuery
    funnelsFilter: FunnelsFilter
    breakdownFilter: BreakdownFilter

    interval: IntervalType

    breakdown: List[Union[str, int]] | None
    breakdownType: BreakdownType
    breakdownAttributionType: BreakdownAttributionType

    funnelWindowInterval: int
    funnelWindowIntervalUnit: FunnelConversionWindowTimeUnit

    actorsQuery: FunnelsActorsQuery | None

    includeTimestamp: Optional[bool]
    includePrecedingTimestamp: Optional[bool]
    includeProperties: List[str]
    includeFinalMatchingEvents: Optional[bool]

    def __init__(
        self,
        query: FunnelsQuery,
        team: Team,
        timings: Optional[HogQLTimings] = None,
        modifiers: Optional[HogQLQueryModifiers] = None,
        limit_context: Optional[LimitContext] = None,
        include_timestamp: Optional[bool] = None,
        include_preceding_timestamp: Optional[bool] = None,
        include_properties: Optional[List[str]] = None,
        include_final_matching_events: Optional[bool] = None,
    ):
        super().__init__(query=query, team=team, timings=timings, modifiers=modifiers, limit_context=limit_context)

        self.funnelsFilter = self.query.funnelsFilter or FunnelsFilter()
        self.breakdownFilter = self.query.breakdownFilter or BreakdownFilter()

        # defaults
        self.interval = self.query.interval or IntervalType.day

        self.breakdownType = self.breakdownFilter.breakdown_type or BreakdownType.event
        self.breakdownAttributionType = (
            self.funnelsFilter.breakdownAttributionType or BreakdownAttributionType.first_touch
        )
        self.funnelWindowInterval = self.funnelsFilter.funnelWindowInterval or 14
        self.funnelWindowIntervalUnit = (
            self.funnelsFilter.funnelWindowIntervalUnit or FunnelConversionWindowTimeUnit.day
        )

        self.includeTimestamp = include_timestamp
        self.includePrecedingTimestamp = include_preceding_timestamp
        self.includeProperties = include_properties or []
        self.includeFinalMatchingEvents = include_final_matching_events

        # the API accepts either:
        #   a string (single breakdown) in parameter "breakdown"
        #   a list of numbers (one or more cohorts) in parameter "breakdown"
        #   a list of strings (multiple breakdown) in parameter "breakdowns"
        # if the breakdown is a string, box it as a list to reduce paths through the code
        #
        # The code below ensures that breakdown is always an array
        # without it affecting the multiple areas of the code outside of funnels that use breakdown
        #
        # Once multi property breakdown is implemented in Trends this becomes unnecessary

        # if isinstance(self._filter.breakdowns, List) and self._filter.breakdown_type in [
        #     "person",
        #     "event",
        #     "hogql",
        #     None,
        # ]:
        #     data.update({"breakdown": [b.get("property") for b in self._filter.breakdowns]})

        if isinstance(self.breakdownFilter.breakdown, str) and self.breakdownType in [
            "person",
            "event",
            "hogql",
            None,
        ]:
            boxed_breakdown: List[Union[str, int]] = box_value(self.breakdownFilter.breakdown)
            self.breakdown = boxed_breakdown
        else:
            self.breakdown = self.breakdownFilter.breakdown  # type: ignore

        self.actorsQuery = None

    @cached_property
    def max_steps(self) -> int:
        return len(self.query.series)
