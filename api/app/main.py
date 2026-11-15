import os
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, Boolean, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./recurshield.db')
RECOMMENDER_URL = os.getenv('RECOMMENDER_URL', 'http://recommender:8001')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False, default='Other')
    amount = Column(Numeric(12,2), nullable=False)
    previous_amount = Column(Numeric(12,2), nullable=True)
    billing_cycle = Column(String(16), nullable=False)
    next_billing_date = Column(Date, nullable=False)
    last_used_date = Column(Date, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

Base.metadata.create_all(bind=engine)

class SubscriptionIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default='Other', max_length=80)
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    previous_amount: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    billing_cycle: str
    next_billing_date: date
    last_used_date: Optional[date] = None
    active: bool = True

class SubscriptionOut(SubscriptionIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

app = FastAPI(title='RecurShield Core API', version='0.1.0')

def db_session():
    with SessionLocal() as db:
        yield db

def as_payload(item: Subscription):
    return SubscriptionOut.model_validate(item).model_dump(mode='json')

@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'core-api'}

@app.get('/api/subscriptions', response_model=list[SubscriptionOut])
def list_subscriptions(db: Session=Depends(db_session)):
    return db.scalars(select(Subscription).order_by(Subscription.id)).all()

@app.post('/api/subscriptions', response_model=SubscriptionOut, status_code=201)
def create_subscription(payload: SubscriptionIn, db: Session=Depends(db_session)):
    if payload.billing_cycle not in ('monthly','yearly'):
        raise HTTPException(422, 'billing_cycle must be monthly or yearly')
    record = Subscription(**payload.model_dump())
    db.add(record); db.commit(); db.refresh(record)
    return record

@app.delete('/api/subscriptions/{subscription_id}', status_code=204)
def remove_subscription(subscription_id: int, db: Session=Depends(db_session)):
    record = db.get(Subscription,subscription_id)
    if record is None: raise HTTPException(404,'Subscription not found')
    db.delete(record); db.commit()

@app.get('/api/summary')
def summary(db: Session=Depends(db_session)):
    items = db.scalars(select(Subscription).where(Subscription.active.is_(True))).all()
    monthly = sum((Decimal(s.amount) / (12 if s.billing_cycle == 'yearly' else 1) for s in items), Decimal('0'))
    return {'active_count':len(items), 'monthly_total':float(round(monthly,2)), 'annual_projection':float(round(monthly*12,2)), 'currency':'USD'}

@app.get('/api/recommendations')
async def recommendations(db: Session=Depends(db_session)):
    items = db.scalars(select(Subscription).where(Subscription.active.is_(True))).all()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(f'{RECOMMENDER_URL}/analyze', json={'subscriptions':[as_payload(s) for s in items]})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        raise HTTPException(503,'Recommendation engine unavailable')

@app.post('/api/demo/seed')
def seed_demo(db: Session=Depends(db_session)):
    if db.scalar(select(Subscription.id).limit(1)):
        return {'message':'Database already contains subscriptions'}
    today = date.today()
    examples = [
        Subscription(name='StreamBox',category='Streaming',amount=Decimal('15.99'),previous_amount=Decimal('12.99'),billing_cycle='monthly',next_billing_date=today+timedelta(days=5),last_used_date=today-timedelta(days=65)),
        Subscription(name='StreamBox Plus',category='Streaming',amount=Decimal('9.99'),billing_cycle='monthly',next_billing_date=today+timedelta(days=12),last_used_date=today-timedelta(days=2)),
        Subscription(name='Cloud Vault',category='Storage',amount=Decimal('119.88'),billing_cycle='yearly',next_billing_date=today+timedelta(days=25),last_used_date=today-timedelta(days=1)),
    ]
    db.add_all(examples);db.commit()
    return {'message':'Three demonstration subscriptions added', 'count':3}
