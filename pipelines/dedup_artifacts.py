"""dedup_artifacts.py

Data quality job that detects and reports duplicate artifact records
in middle_earth.artifacts.

Runs weekly via Databricks Job (job_id: 9391). Identifies duplicates
by artifact name and logs them for manual review.

Owner: Middle-earth Data Engineering Team
Schedule: Weekly, Sundays 06:00 UTC
Last reviewed: 3019-03-15
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

CATALOG = "fo_omnigent_demo_catalog"
PROD_SCHEMA = f"{CATALOG}.middle_earth"


def get_spark():
    return SparkSession.builder.getOrCreate()


def find_duplicates(spark, schema=PROD_SCHEMA):
    """Find artifacts with duplicate names."""
    artifacts = spark.table(f"{schema}.artifacts")

    # Window to count occurrences of each artifact name
    name_window = Window.partitionBy("name")

    dupes = artifacts.withColumn(
        "name_count", F.count("*").over(name_window)
    ).filter(
        F.col("name_count") > 1
    ).orderBy("name", "artifact_id")

    return dupes


def generate_report(dupes_df):
    """Generate a dedup report for manual review."""
    report_rows = dupes_df.select(
        "artifact_id", "name", "bearer", "status", "current_location"
    ).collect()

    if not report_rows:
        print("No duplicates found.")
        return

    print("=" * 60)
    print("DUPLICATE ARTIFACT REPORT")
    print("=" * 60)
    for row in report_rows:
        print(f"  ID: {row.artifact_id} | {row.name}")
        print(f"    Bearer: {row.bearer} | Status: {row.status}")
        print(f"    Location: {row.current_location}")
        print()
    print(f"Total duplicate records: {len(report_rows)}")
    print("Action required: Manual review and cleanup.")
    print("=" * 60)


def main():
    """Main entry point."""
    spark = get_spark()

    print(f"Scanning {PROD_SCHEMA}.artifacts for duplicates...")
    dupes = find_duplicates(spark)
    dupe_count = dupes.count()
    print(f"Found {dupe_count} duplicate records.")

    if dupe_count > 0:
        generate_report(dupes)


if __name__ == "__main__":
    main()
