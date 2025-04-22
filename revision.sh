docker compose exec l4d2vortexapi alembic revision --autogenerate
# docker cp l4d2vortexapi:/app/src/migrations/versions/[миграция] /root/api-vortex/src/migrations/versions/