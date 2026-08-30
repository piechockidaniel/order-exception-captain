"""HTTP boundary for the offline, approval-gated demo service."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .domain import AuditEvent, DryRunPreview, Incident, Order
from .dry_run import DryRunOutboundAdapter
from .persistence import SqliteIncidentRepository
from .redaction import redact_event_for_operator, redact_incident_for_operator
from .scanning import IncidentScanService, ScanResult
from .sample_data import demo_orders
from .workflow import DeterministicCoordinator, TemplateSpecialistRunner


class ScanRequest(BaseModel):
    orders: list[Order]


class ApprovalRequest(BaseModel):
    operator: str = Field(min_length=1, max_length=120)


class RejectionRequest(ApprovalRequest):
    reason: str = Field(min_length=3, max_length=500)


def create_app(database_path: str | Path) -> FastAPI:
    """Create an application with an explicit database location for simple testing and deployment."""
    repository = SqliteIncidentRepository(database_path)
    scanner = IncidentScanService(DeterministicCoordinator(TemplateSpecialistRunner()), repository)
    dry_run_adapter = DryRunOutboundAdapter()

    app = FastAPI(
        title="Order Exception Captain",
        version="0.1.0",
        description="A deterministic delivery-exception service that creates approval-gated drafts only.",
    )
    app.state.repository = repository
    dashboard_assets = Path(__file__).parent / "static"
    app.mount("/assets", StaticFiles(directory=dashboard_assets), name="assets")

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(dashboard_assets / "index.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/scans", response_model=ScanResult, status_code=status.HTTP_200_OK)
    def scan(request: ScanRequest) -> ScanResult:
        return scanner.scan(request.orders)

    @app.post("/demo/scan", response_model=ScanResult, status_code=status.HTTP_200_OK)
    def scan_demo_data() -> ScanResult:
        """Populate the local dashboard with reserved-domain, synthetic sample orders."""
        return scanner.scan(demo_orders())

    @app.get("/incidents", response_model=list[Incident])
    def list_incidents() -> list[Incident]:
        return [redact_incident_for_operator(incident) for incident in repository.list_incidents()]

    @app.get("/incidents/{incident_id}", response_model=Incident)
    def get_incident(incident_id: str) -> Incident:
        try:
            return redact_incident_for_operator(repository.get_incident(incident_id))
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.") from error

    @app.post("/incidents/{incident_id}/approve", response_model=Incident)
    def approve(incident_id: str, request: ApprovalRequest) -> Incident:
        try:
            return redact_incident_for_operator(repository.approve(incident_id, request.operator))
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.") from error
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    @app.post("/incidents/{incident_id}/reject", response_model=Incident)
    def reject(incident_id: str, request: RejectionRequest) -> Incident:
        try:
            return redact_incident_for_operator(repository.reject(incident_id, request.operator, request.reason))
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.") from error
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    @app.post("/incidents/{incident_id}/dry-run", response_model=DryRunPreview)
    def prepare_dry_run(incident_id: str, request: ApprovalRequest) -> DryRunPreview:
        try:
            preview = dry_run_adapter.prepare(repository.get_incident(incident_id))
            preview.already_prepared = not repository.record_dry_run(incident_id, request.operator)
            return preview
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.") from error
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    @app.get("/incidents/{incident_id}/events", response_model=list[AuditEvent])
    def list_events(incident_id: str) -> list[AuditEvent]:
        try:
            return [redact_event_for_operator(event) for event in repository.list_events(incident_id)]
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.") from error

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Order Exception Captain API.")
    parser.add_argument("--database", default="data/order-exception-captain.sqlite3")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app = create_app(args.database)
    uvicorn.run(app, host=args.host, port=args.port)
