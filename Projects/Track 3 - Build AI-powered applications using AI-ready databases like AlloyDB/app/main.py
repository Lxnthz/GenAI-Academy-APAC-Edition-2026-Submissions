import os
from contextlib import closing

from flask import Flask, jsonify, request
import psycopg
from psycopg.rows import dict_row


app = Flask(__name__)


def db_conn():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode=os.environ.get("DB_SSLMODE", "require"),
        row_factory=dict_row,
    )


def run_sql(sql_text, params=None):
    with closing(db_conn()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_text, params or ())
            if cur.description:
                return cur.fetchall()
            conn.commit()
            return []


def fallback_sql_from_question(question):
    q = question.lower()
    if "technical support" in q and ("incident" in q or "urgent" in q):
        return """
    select ticket_id, created_at, ticket_type, queue, priority, status, urgency_score, subject
        from support_tickets
    where language = 'en'
      and queue = 'Technical Support'
      and ticket_type = 'incident'
          and status <> 'closed'
          and urgency_score >= 70
      and created_at >= now() - interval '30 days'
        order by urgency_score desc, created_at desc
        limit 50
        """

    if "tag" in q or "outage" in q:
        return """
    select coalesce(tag_1, 'unknown') as top_tag, count(*) as issue_count
        from support_tickets
    where language = 'en'
    group by coalesce(tag_1, 'unknown')
    order by issue_count desc
    limit 10
        """

    if "queue" in q and "urgent" in q:
        return """
    select queue, count(*) as urgent_open_count
        from support_tickets
    where language = 'en'
      and status <> 'closed'
      and urgency_score >= 70
    group by queue
    order by urgent_open_count desc
        limit 10
        """

    return """
        select ticket_id, created_at, ticket_type, queue, priority, status, urgency_score, subject
    from support_tickets
        where language = 'en'
    order by created_at desc
    limit 25
    """


def nl_to_sql(question):
    template = os.environ.get("APP_NL_TO_SQL_TEMPLATE", "").strip()
    if not template:
        return fallback_sql_from_question(question), "fallback"

    nl_sql = template.format(question=question.replace("'", "''"))
    try:
        rows = run_sql(nl_sql)
        if not rows:
            return fallback_sql_from_question(question), "fallback"

        first_value = next(iter(rows[0].values()))
        if not first_value:
            return fallback_sql_from_question(question), "fallback"

        return str(first_value), "alloydb_ai"
    except Exception:
        return fallback_sql_from_question(question), "fallback"


@app.get("/health")
def health():
    try:
        rows = run_sql("select 1 as ok")
        return jsonify({"status": "ok", "db": rows[0]["ok"]})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.get("/")
def home():
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Track 3 AlloyDB AI NL Demo</title>
    <style>
      body { font-family: Segoe UI, Tahoma, sans-serif; margin: 24px; max-width: 960px; }
      textarea { width: 100%; min-height: 96px; }
      button { margin-top: 12px; padding: 10px 16px; }
      pre { background: #f5f5f5; padding: 12px; overflow: auto; }
      .row { margin-top: 16px; }
    </style>
  </head>
  <body>
    <h1>AlloyDB AI Natural Language Demo</h1>
    <p>Ask in plain English. The app shows generated SQL and query results.</p>
    <textarea id="q">Show high-urgency incident tickets in Technical Support for the last 30 days</textarea>
    <br />
    <button onclick="runQuery()">Run Query</button>
    <div class="row">
      <h3>Generated SQL</h3>
      <pre id="sql"></pre>
    </div>
    <div class="row">
      <h3>Source</h3>
      <pre id="src"></pre>
    </div>
    <div class="row">
      <h3>Results</h3>
      <pre id="results"></pre>
    </div>
    <script>
      async function runQuery() {
        const question = document.getElementById('q').value;
        const res = await fetch('/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question })
        });
        const data = await res.json();
        document.getElementById('sql').textContent = data.generated_sql || '';
        document.getElementById('src').textContent = data.source || '';
        document.getElementById('results').textContent = JSON.stringify(data.rows || [], null, 2);
      }
    </script>
  </body>
</html>
    """


@app.post("/query")
def query():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    generated_sql, source = nl_to_sql(question)

    try:
        rows = run_sql(generated_sql)
        return jsonify(
            {
                "question": question,
                "generated_sql": generated_sql,
                "source": source,
                "rows": rows,
                "row_count": len(rows),
            }
        )
    except Exception as exc:
        return jsonify(
            {
                "question": question,
                "generated_sql": generated_sql,
                "source": source,
                "error": str(exc),
            }
        ), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
