class WorkflowTransformer:

    @staticmethod
    def transform(rows: list[dict]) -> list[dict]:
        workflow_map: dict[str, dict] = {}

        for row in rows:
            workflow_name = row["workflowName"]

            if workflow_name not in workflow_map:
                workflow_map[workflow_name] = {
                    "workflowName": workflow_name,
                    "steps": [],
                }

            workflow_map[workflow_name]["steps"].append(
                {
                    "order": int(row["order"]),
                    "stepName": row["stepName"],
                    "maxResponseHours": int(row["maxResponseHours"]),
                    "requiresNote": str(row["requiresNote"]).lower() == "yes",
                    "autoEscalate": str(row["autoEscalate"]).lower() == "yes",
                }
            )

        return list(workflow_map.values())
