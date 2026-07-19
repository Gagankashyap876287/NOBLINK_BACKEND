from motor.motor_asyncio import AsyncIOMotorCollection

from app.database.mongodb import mongodb


class Collections:

    @staticmethod
    def sensor_pings() -> AsyncIOMotorCollection:
        return mongodb.database.sensor_pings

    @staticmethod
    def sensor_registry() -> AsyncIOMotorCollection:
        return mongodb.database.sensor_registry

    @staticmethod
    def alert_rules() -> AsyncIOMotorCollection:
        return mongodb.database.alert_rules

    @staticmethod
    def workflow_configs() -> AsyncIOMotorCollection:
        return mongodb.database.workflow_configs

    @staticmethod
    def coordinators() -> AsyncIOMotorCollection:
        return mongodb.database.coordinators

    @staticmethod
    def visits() -> AsyncIOMotorCollection:
        return mongodb.database.visits

    @staticmethod
    def alerts() -> AsyncIOMotorCollection:
        return mongodb.database.alerts

    @staticmethod
    def alert_event_logs() -> AsyncIOMotorCollection:
        return mongodb.database.alert_event_logs