import subprocess
import json
from datetime import datetime
import os
import snowflake.connector

LAST_SYNC_FILE = "last_sync.json"
EXPORT_PATH = "/tmp"
SNOWFLAKE_CONFIG = {
    "user": "student",
    "database": "SF_SAMPLE",
    "schema": "PUBLIC"
}


def load_last_sync_time():
    if os.path.exists(LAST_SYNC_FILE):
        with open(LAST_SYNC_FILE) as f:
            return json.load(f)["last_synced"]
    return "2000-01-01T00:00:00Z"


def save_sync_time():
    with open(LAST_SYNC_FILE, "w") as f:
        json.dump({"last_synced": datetime.utcnow().isoformat()}, f)


def export_collection(collection, fields, since_time):
    out_file_container = f"/tmp/{collection}.csv"
    out_file_host = f"./{collection}.csv"  # Local path to copy to
    fields_str = ",".join(fields)

    # Export inside container
    cmd = [
        "docker", "exec", "mongodb", "mongoexport",
        "--db=btc_bet",
        f"--collection={collection}",
        "--type=csv",
        f"--out={out_file_container}",
        f"--query={{\"created_at\":{{\"$gt\":\"{since_time}\"}}}}",
        f"--fields={fields_str}"
    ]
    subprocess.run(cmd, check=True)

    # Copy from Docker container to host
    subprocess.run([
        "docker", "cp", f"mongodb:{out_file_container}", out_file_host
    ], check=True)

    return out_file_host

def upload_to_snowflake(file_path, table):
    ctx = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cs = ctx.cursor()
    with cs:
        cs.execute(f"PUT file://{file_path} @%{table}")
        cs.execute(f"COPY INTO {table} FILE_FORMAT=(TYPE=CSV FIELD_OPTIONALLY_ENCLOSED_BY='\"' SKIP_HEADER=1)")
    ctx.close()


def run_incremental_sync():
    last_sync = load_last_sync_time()

    user_fields = ["user_id", "balance", "active_bets", "created_at"]
    bet_fields = ["user_id", "guess", "block_height", "status", "created_at"]

    users_file = export_collection("users", user_fields, last_sync)
    bets_file = export_collection("bets", bet_fields, last_sync)

    upload_to_snowflake(users_file, "bets_app_users")
    upload_to_snowflake(bets_file, "bets_app_bets")

    save_sync_time()


if __name__ == "__main__":
    run_incremental_sync()
