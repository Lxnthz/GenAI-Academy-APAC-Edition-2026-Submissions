import csv
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg


def main():
    db_host = os.environ["DB_HOST"]
    db_port = int(os.environ.get("DB_PORT", "5432"))
    db_name = os.environ.get("DB_NAME", "postgres")
    db_user = os.environ["DB_USER"]
    db_password = os.environ["DB_PASSWORD"]

    root = Path(__file__).resolve().parents[1]
    csv_path = Path(os.environ.get("DATASET_PATH", str(root / "data" / "it_support_ticket_en.csv")))
    seed_limit = int(os.environ.get("SEED_LIMIT", "10000"))

    base_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)

    def norm(value, fallback=""):
        return (value or fallback).strip()

    def infer_status(ticket_type, priority):
        t = ticket_type.lower()
        p = priority.lower()
        if t == "request" and p == "low":
            return "closed"
        if t == "change":
            return "pending"
        return "open"

    def infer_region(queue_name):
        q = queue_name.lower()
        if "billing" in q:
            return "finance"
        if "sales" in q:
            return "sales"
        if "outage" in q or "maintenance" in q:
            return "platform"
        if "technical" in q or "it" in q:
            return "ops"
        return "support"

    def infer_channel(queue_name):
        q = queue_name.lower()
        if "technical" in q or "it" in q:
            return "portal"
        if "sales" in q:
            return "email"
        return "chat"

    def infer_sentiment(priority):
        p = priority.lower()
        if p == "critical":
            return -0.9
        if p == "high":
            return -0.6
        if p == "medium":
            return -0.3
        return -0.1

    def infer_resolution_hours(status, priority):
        if status != "closed":
            return None
        p = priority.lower()
        if p == "high":
            return 8.0
        if p == "medium":
            return 16.0
        return 24.0

    with psycopg.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password,
        sslmode=os.environ.get("DB_SSLMODE", "require"),
    ) as conn:
        with conn.cursor() as cur:
            with csv_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = []
                for idx, r in enumerate(reader, start=1):
                    if seed_limit > 0 and idx > seed_limit:
                        break

                    language = norm(r.get("language"), "en").lower()
                    if language != "en":
                        continue

                    priority = norm(r.get("priority"), "medium").lower()
                    ticket_type = norm(r.get("type"), "incident")
                    queue_name = norm(r.get("queue"), "Technical Support")
                    status = infer_status(ticket_type, priority)

                    subject = norm(r.get("subject"), "No subject")
                    body = norm(r.get("body"), "")
                    answer = norm(r.get("answer"), "")

                    ticket_id = idx
                    customer_id = f"CUST-{(abs(hash(subject)) % 2000) + 1:04d}"
                    created_at = (base_dt + timedelta(hours=idx * 2)).isoformat()
                    category = ticket_type.lower()
                    channel = infer_channel(queue_name)
                    region = infer_region(queue_name)
                    customer_sentiment = infer_sentiment(priority)
                    resolution_time_hours = infer_resolution_hours(status, priority)

                    version_raw = norm(r.get("version"), "0")
                    version = int(version_raw) if version_raw.isdigit() else None

                    rows.append(
                        (
                            ticket_id,
                            customer_id,
                            created_at,
                            category,
                            channel,
                            region,
                            priority,
                            status,
                            resolution_time_hours,
                            customer_sentiment,
                            subject,
                            body,
                            answer,
                            ticket_type,
                            queue_name,
                            language,
                            version,
                            norm(r.get("tag_1")),
                            norm(r.get("tag_2")),
                            norm(r.get("tag_3")),
                            norm(r.get("tag_4")),
                            norm(r.get("tag_5")),
                            norm(r.get("tag_6")),
                            norm(r.get("tag_7")),
                            norm(r.get("tag_8")),
                        )
                    )

            cur.executemany(
                """
                insert into support_tickets (
                  ticket_id, customer_id, created_at, category, channel,
                  region, priority, status, resolution_time_hours, customer_sentiment,
                  subject, body, answer, ticket_type, queue, language, version,
                  tag_1, tag_2, tag_3, tag_4, tag_5, tag_6, tag_7, tag_8
                )
                values (
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s
                )
                on conflict (ticket_id) do update
                set customer_id = excluded.customer_id,
                    created_at = excluded.created_at,
                    category = excluded.category,
                    channel = excluded.channel,
                    region = excluded.region,
                    priority = excluded.priority,
                    status = excluded.status,
                    resolution_time_hours = excluded.resolution_time_hours,
                    customer_sentiment = excluded.customer_sentiment,
                    subject = excluded.subject,
                    body = excluded.body,
                    answer = excluded.answer,
                    ticket_type = excluded.ticket_type,
                    queue = excluded.queue,
                    language = excluded.language,
                    version = excluded.version,
                    tag_1 = excluded.tag_1,
                    tag_2 = excluded.tag_2,
                    tag_3 = excluded.tag_3,
                    tag_4 = excluded.tag_4,
                    tag_5 = excluded.tag_5,
                    tag_6 = excluded.tag_6,
                    tag_7 = excluded.tag_7,
                    tag_8 = excluded.tag_8
                """,
                rows,
            )

        conn.commit()

    print(f"Loaded {len(rows)} rows from {csv_path}")


if __name__ == "__main__":
    main()
