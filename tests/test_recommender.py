from datetime import date,timedelta
from decimal import Decimal
from recommender.app.main import analyze, Subscription

def test_cost_issues_and_due_date():
    now=date(2026,11,14)
    items=[
      Subscription(id=1,name='A',category='Streaming',amount=Decimal('15.99'),previous_amount=Decimal('10.00'),billing_cycle='monthly',next_billing_date=now+timedelta(days=3),last_used_date=now-timedelta(days=60)),
      Subscription(id=2,name='B',category='Streaming',amount=Decimal('7.00'),billing_cycle='monthly',next_billing_date=now+timedelta(days=30)),
    ]
    result=analyze(items,now)
    types={a['type'] for a in result['alerts']}
    assert types=={'price_increase','underused','upcoming_bill','possible_overlap'}

def test_inactive_does_not_trigger():
    now=date(2026,11,14)
    item=Subscription(id=1,name='X',category='Software',amount=Decimal('10'),previous_amount=Decimal('5'),billing_cycle='monthly',next_billing_date=now,active=False)
    assert analyze([item],now)['alerts']==[]
