"""sync_event_outcomes.py

ETL pipeline that reads event outcomes from middle_earth.events and updates
character statuses in middle_earth.characters accordingly.

Runs nightly via Databricks Job (job_id: 9384). Reads events, maps outcomes
to character status changes, and merges updates.

Owner: Middle-earth Data Engineering Team
Schedule: Daily 02:00 UTC
Last reviewed: 3019-03-15
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

CATALOG = "fo_omnigent_demo_catalog"
PROD_SCHEMA = f"{CATALOG}.middle_earth"
SANDBOX_SCHEMA = f"{CATALOG}.middle_earth_sandbox"


def get_spark():
    return SparkSession.builder.getOrCreate()


def load_events(spark, schema=PROD_SCHEMA):
    """Load all events from the events table."""
    return spark.table(f"{schema}.events")


def determine_status_from_outcome(outcome):
    """Map event outcomes to character status changes.

    Returns a new status string if the outcome implies a status change,
    or None if no change is warranted.
    """
    death_keywords = ["falls", "destroyed", "defeated", "slain"]
    departure_keywords = ["departed", "sailed"]

    outcome_lower = outcome.lower() if outcome else ""
    for kw in death_keywords:
        if kw in outcome_lower:
            return "Deceased"
    for kw in departure_keywords:
        if kw in outcome_lower:
            return "Departed"
    return None


status_udf = F.udf(determine_status_from_outcome, StringType())


def extract_status_updates(events_df):
    """Extract character status updates from event outcomes.

    Explodes the participants array so each character gets evaluated
    against the event outcome.
    """
    exploded = events_df.select(
        F.col("event_id"),
        F.col("event_name"),
        F.col("outcome"),
        F.col("date"),
        F.explode(F.col("participants")).alias("character_name")
    )

    with_status = exploded.withColumn(
        "new_status", status_udf(F.col("outcome"))
    ).filter(
        F.col("new_status").isNotNull()
    )

    return with_status


def apply_updates(spark, updates_df, target_schema=PROD_SCHEMA):
    """Merge status updates into the characters table."""
    characters = spark.table(f"{target_schema}.characters")

    merged = characters.join(
        updates_df.select("character_name", "new_status", "date"),
        characters.name == updates_df.character_name,
        "left"
    ).select(
        characters["*"],
        F.coalesce(updates_df["new_status"], characters["status"]).alias("updated_status"),
        F.coalesce(updates_df["date"], characters["last_updated"].cast("string")).alias("updated_date")
    )

    merged.select(
        F.col("character_id"),
        F.col("name"),
        F.col("race"),
        F.col("allegiance"),
        F.col("home_location"),
        F.col("home_address"),
        F.col("role"),
        F.col("updated_status").alias("status"),
        F.col("updated_date").cast("timestamp").alias("last_updated")
    ).write.mode("overwrite").saveAsTable(f"{target_schema}.characters")


def main(target_schema=PROD_SCHEMA):
    """Main pipeline entry point."""
    spark = get_spark()

    print(f"[sync_event_outcomes] Loading events from {target_schema}...")
    events = load_events(spark, schema=target_schema)
    event_count = events.count()
    print(f"[sync_event_outcomes] Loaded {event_count} events")

    print("[sync_event_outcomes] Extracting status updates...")
    updates = extract_status_updates(events)
    update_count = updates.count()
    print(f"[sync_event_outcomes] Found {update_count} status updates to apply")

    if update_count > 0:
        print(f"[sync_event_outcomes] Applying updates to {target_schema}.characters...")
        apply_updates(spark, updates, target_schema)
        print("[sync_event_outcomes] Complete.")
    else:
        print("[sync_event_outcomes] No updates to apply.")


if __name__ == "__main__":
    main()
