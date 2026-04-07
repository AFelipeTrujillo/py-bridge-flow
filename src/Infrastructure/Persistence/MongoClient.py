from motor.motor_asyncio import AsyncIOMotorClient

def get_mongodb_client(uri: str):
    """Initializes the asynchronous Mongo client."""
    return AsyncIOMotorClient(uri)

def get_database(client: AsyncIOMotorClient, db_name: str):
    """Returns the specific database instance."""
    return client[db_name]