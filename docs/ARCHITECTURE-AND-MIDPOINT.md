# Architecture and midpoint evidence map

## Original Deliverable 1
The seven-page report proposes React/TypeScript + NGINX frontend, FastAPI Core API, dedicated recommendation service, PostgreSQL with persistent storage, Redis caching, Kubernetes deployments, internal ClusterIP networking, config/secret separation, and multi-platform Docker images. It identifies CloudLab as a potential deployment platform and GitHub Actions as CI/CD.

## Midpoint architecture (implemented as templates/code)
Browser → NodePort/NGINX → FastAPI Core API → PostgreSQL; API → recommendation engine. Redis is deployed but its cache is **not integrated**. No TLS Ingress or authentication yet.

## Changes and justification
The prototype intentionally uses manually entered subscription data rather than real bank integrations to validate the database, API, recommendation rules, and container networking without exposing sensitive financial records. Initial deployment uses NodePort in place of TLS Ingress, as explicitly allowed for class testing. Automation covers tests and image builds but **does not publish images or deploy**.

## Demonstrable technical activities
- Show `POST /api/demo/seed`, GET list, summary, and recommendation responses.
- Recommender tests distinguish price increase, underused item, upcoming renewal, and overlapping category.
- Show database persistence by restarting the DB and API and retrieving unchanged subscription records.
- Show `kubectl get ...` only after deployment is actually verified.

## Limitations and further work
Authentication, bank sync, Redis integration, security boundaries, metrics, production Ingress, CI publishing/deployment, robust database migrations, concurrency/rate limits and high availability are out of scope for current starter.
