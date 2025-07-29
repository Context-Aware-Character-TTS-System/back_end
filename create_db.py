import database, models

print("Creating database tables...")
models.Base.metadata.create_all(bind=database.engine)
print("Database tables created.")
