docker compose exec l4d2vortexapi alembic revision --autogenerate -m "Update"
# docker cp l4d2vortexapi:/app/src/migrations/versions/[миграция] /root/api-vortex/src/migrations/versions/