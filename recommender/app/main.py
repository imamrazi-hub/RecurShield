from datetime import date
from decimal import Decimal
from collections import defaultdict
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title='RecurShield Recommendation Engine',version='0.1.0')

class Subscription(BaseModel):
    id: int
    name: str
    category: str = 'Other'
    amount: Decimal = Field(ge=0)
    previous_amount: Decimal | None = None
    billing_cycle: str
    next_billing_date: date
    last_used_date: date | None = None
    active: bool = True

class AnalyzeRequest(BaseModel):
    subscriptions: list[Subscription]

@app.get('/health')
def health():return {'status':'ok','service':'recommender'}

def analyze(items: list[Subscription],today: date | None=None):
    today=today or date.today()
    alerts=[]
    categories=defaultdict(list)
    for s in items:
        if not s.active:continue
        categories[s.category.strip().casefold()].append(s)
        if s.previous_amount is not None and s.amount > s.previous_amount:
            alerts.append({'subscription_id':s.id,'type':'price_increase','message':f'{s.name} increased from ${s.previous_amount:.2f} to ${s.amount:.2f}.','action':'Review price change'})
        if s.last_used_date is not None and (today-s.last_used_date).days>=45:
            alerts.append({'subscription_id':s.id,'type':'underused','message':f'{s.name} has not been used in {(today-s.last_used_date).days} days.','action':'Consider cancelling or downgrading'})
        days=(s.next_billing_date-today).days
        if 0<=days<=7:
            alerts.append({'subscription_id':s.id,'type':'upcoming_bill','message':f'{s.name} renews in {days} days.','action':'Review before renewal'})
    for category,group in categories.items():
        if len(group)>1:
            alerts.append({'subscription_id':None,'type':'possible_overlap','message':f'{len(group)} subscriptions share the {category} category.','action':'Check for overlapping services'})
    return {'alerts':alerts,'alert_count':len(alerts),'disclaimer':'Rule-based suggestions only; no bank transactions or personal usage are automatically verified.'}

@app.post('/analyze')
def analyze_endpoint(body:AnalyzeRequest):return analyze(body.subscriptions)
