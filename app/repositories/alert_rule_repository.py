from app.database.collections import Collections


class AlertRuleRepository:

    def __init__(self):

        self.collection = Collections.alert_rules()

    async def get_enabled_rules(self):

        return await self.collection.find(
            {
                "enabled": True
            }
        ).to_list(None)