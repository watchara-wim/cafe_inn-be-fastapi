from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.table import Table
from app.schemas.table import TableResponse

router = APIRouter()


@router.get("/", response_model=list[TableResponse])
def get_all_tables(db: Session = Depends(get_db)):
    tables = db.query(Table).all()
    return tables
