from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.email_utils import send_report_email
from app.pdf import render_visit_pdf

router = APIRouter(prefix="/visits", tags=["visits"])


def _get_visit_or_404(db: Session, visit_id: str) -> models.Visit:
    visit = crud.get_visit(db, visit_id)
    if visit is None:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


def _generate_and_send(db: Session, visit: models.Visit, lang: str | None = None) -> models.Visit:
    visit_dict = crud.serialize_visit(db, visit)
    try:
        pdf_bytes = render_visit_pdf(visit_dict, lang)
        send_report_email(visit_dict, pdf_bytes, lang)
    except Exception as exc:  # noqa: BLE001 - report any failure back to the user
        return crud.set_email_status(db, visit, sent=False, error=str(exc))
    return crud.set_email_status(db, visit, sent=True, error=None)


@router.post("", response_model=schemas.VisitOut)
def create_visit(data: schemas.VisitIn, lang: str = "en", db: Session = Depends(get_db)):
    visit = crud.create_visit(db, data)
    visit = _generate_and_send(db, visit, lang)
    return crud.serialize_visit(db, visit)


@router.get("", response_model=list[schemas.VisitListItem])
def list_visits(
    search: str | None = None,
    city: str | None = None,
    surveyor_name: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_visits(
        db, search=search, city=city, surveyor_name=surveyor_name, date_from=date_from, date_to=date_to
    )


@router.get("/{visit_id}", response_model=schemas.VisitOut)
def get_visit(visit_id: str, db: Session = Depends(get_db)):
    visit = _get_visit_or_404(db, visit_id)
    return crud.serialize_visit(db, visit)


@router.put("/{visit_id}", response_model=schemas.VisitOut)
def update_visit(visit_id: str, data: schemas.VisitIn, lang: str = "en", db: Session = Depends(get_db)):
    visit = _get_visit_or_404(db, visit_id)
    visit = crud.update_visit(db, visit, data)
    visit = _generate_and_send(db, visit, lang)
    return crud.serialize_visit(db, visit)


@router.delete("/{visit_id}", status_code=204)
def delete_visit(visit_id: str, db: Session = Depends(get_db)):
    visit = _get_visit_or_404(db, visit_id)
    crud.delete_visit(db, visit)


@router.post("/{visit_id}/resend-email", response_model=schemas.VisitOut)
def resend_email(visit_id: str, lang: str = "en", db: Session = Depends(get_db)):
    visit = _get_visit_or_404(db, visit_id)
    visit = _generate_and_send(db, visit, lang)
    return crud.serialize_visit(db, visit)


@router.get("/{visit_id}/pdf")
def download_pdf(visit_id: str, lang: str = "en", db: Session = Depends(get_db)):
    visit = _get_visit_or_404(db, visit_id)
    visit_dict = crud.serialize_visit(db, visit)
    pdf_bytes = render_visit_pdf(visit_dict, lang)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="measurement-{visit_id}.pdf"'},
    )
