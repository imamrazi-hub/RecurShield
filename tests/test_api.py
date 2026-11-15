import os
os.environ['DATABASE_URL']='sqlite://'
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from api.app import main as m

m.engine.dispose()
m.engine = __import__('sqlalchemy').create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
m.SessionLocal.configure(bind=m.engine)
m.Base.metadata.create_all(m.engine)
client=TestClient(m.app)

def test_subscription_crud_and_summary():
    body={'name':'Test','category':'Software','amount':120.00,'billing_cycle':'yearly','next_billing_date':'2027-01-01','active':True}
    response=client.post('/api/subscriptions',json=body)
    assert response.status_code==201
    item=response.json()
    assert item['name']=='Test'
    summary=client.get('/api/summary').json()
    assert summary['active_count']==1
    assert summary['monthly_total']==10.0
    assert client.delete(f"/api/subscriptions/{item['id']}").status_code==204
    assert client.get('/api/summary').json()['active_count']==0
