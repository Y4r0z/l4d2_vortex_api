docker compose exec l4d2vortexapi alembic revision --autogenerate -m "Update Name"
# docker cp l4d2vortexapi:миграция /root/api-vortex/src/migrations/versions/