from __future__ import annotations

from orchestra.conductor.landing.land import LandingResult, LandRequest


class Adapter:
    def run(self, request: LandRequest) -> LandingResult:
        del request
        return LandingResult("skipped", 0, "", "", (), ("example adapter",))
