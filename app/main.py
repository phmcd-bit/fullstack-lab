"""API de eventos usada em todas as etapas do projeto."""

from datetime import date
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database import Base, make_engine
from app.models import Event, Registration
from app.db_session import get_session
from app.registrations import router

class EventInput(BaseModel):
    """Dados enviados pelo cliente ao cadastrar um evento."""

    title: str
    date: date
    capacity: int


def create_app(database_url: str = "sqlite://") -> FastAPI:
    """Cria uma API com dados isolados para cada execução ou teste."""
    app = FastAPI(title="Eventos do Trilha")
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    app.state.engine = engine
    app.include_router(router)

    def event_to_dict(session, event):
        used = session.scalar(
            select(func.count()).select_from(Registration).where(Registration.event_id == event.id)
        )
        return {"id": event.id, "title": event.title, "date": event.date, "capacity": event.capacity, "available_slots": event.capacity - used}

    @app.get("/events")
    def list_events(session: Session = Depends(get_session)):
        events = session.scalars(select(Event)).all()  
        resultado = []
        for event in events:
            resultado.append(event_to_dict(session, event))
        return resultado

    @app.get("/events/{event_id}")
    def get_event(event_id: int, session: Session = Depends(get_session)):
        event = session.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Evento não encontrado")
        return event_to_dict(session, event)

    @app.post("/events", status_code=201)
    def create_event(data: EventInput, session: Session = Depends(get_session)):
        if not data.title:
            raise HTTPException(status_code=422, detail="Título é obrigatório")
        if data.capacity <= 0:
            raise HTTPException(status_code=422, detail="Capacidade deve ser um número positivo")

        event = Event(title=data.title, date=data.date, capacity=data.capacity)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event_to_dict(session, event)
    
    return app


app = create_app("sqlite:///events.db")