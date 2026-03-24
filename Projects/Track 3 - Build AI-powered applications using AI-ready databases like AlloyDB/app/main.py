import os
import csv
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def seed_database():
    """Create schema and load CSV data on startup if table is empty."""
    try:
        # Check if table has data
        result = run_sql("SELECT COUNT(*) as cnt FROM support_tickets")
        if result and result[0]["cnt"] > 0:
            print(f"✓ Database already seeded ({result[0]['cnt']} rows)")
            return
        
        print("Initializing database schema...")
        
        # Create schema
        schema_sql = """
        create table if not exists support_tickets (
          ticket_id bigint primary key,
          customer_id text not null,
          created_at timestamptz not null,
          category text not null,
          channel text not null,
          region text not null,
          priority text not null,
          status text not null,
          resolution_time_hours numeric(10,2),
          customer_sentiment numeric(4,2) not null,
          subject text not null,
          body text not null,
          answer text not null,
          ticket_type text not null,
          queue text not null,
          language text not null,
          version int,
          tag_1 text,
          tag_2 text,
          tag_3 text,
          tag_4 text,
          tag_5 text,
          tag_6 text,
          tag_7 text,
          tag_8 text,
          urgency_score int generated always as (
            least(
              100,
              greatest(
                0,
                (
                  case priority
                    when 'critical' then 60
                    when 'high' then 45
                    when 'medium' then 25
                    else 10
                  end
                  + case when status <> 'closed' then 20 else 0 end
                  + case when customer_sentiment < -0.5 then 20 when customer_sentiment < 0 then 10 else 0 end
                )
              )
            )
          ) stored,
          urgency_bucket text default 'medium'
        );
        
        create index if not exists idx_support_tickets_created_at on support_tickets (created_at desc);
        create index if not exists idx_support_tickets_status on support_tickets (status);
        create index if not exists idx_support_tickets_category on support_tickets (category);
        create index if not exists idx_support_tickets_region on support_tickets (region);
        create index if not exists idx_support_tickets_queue on support_tickets (queue);
        create index if not exists idx_support_tickets_language on support_tickets (language);
        """
        run_sql(schema_sql)
        print("✓ Schema created")
        
        # Load CSV data
        root = Path(__file__).resolve().parents[1]
        csv_path = root / "data" / "it_support_ticket_en.csv"
        seed_limit = int(os.environ.get("SEED_LIMIT", "5000"))
        
        if not csv_path.exists():
            print(f"⚠ CSV not found at {csv_path}, skipping data load")
            return
        
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
        
        print(f"Loading CSV from {csv_path}...")
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
                
                rows.append((
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
                ))
        
        if rows:
            with closing(db_conn()) as conn:
                with conn.cursor() as cur:
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
            print(f"✓ Loaded {len(rows)} rows into support_tickets")
    except Exception as e:
        print(f"⚠ Seed warning: {e}")


def fallback_sql_from_question(question):
    q = question.lower()
    if "incident" in q or ("urgent" in q and "ticket" in q):
        return """
    select ticket_id, created_at, ticket_type, queue, priority, status, urgency_score, subject
        from support_tickets
    where language = 'en'
      and (ticket_type = 'incident' or ticket_type = 'Incident')
      and (status = 'open' or status = 'pending')
      and urgency_score >= 50
        order by urgency_score desc, created_at desc
        limit 50
        """

    if "category" in q or "tag" in q or "top" in q:
        return """
    select category, count(*) as count
        from support_tickets
    where language = 'en'
    group by category
    order by count desc
    limit 15
        """

    if "queue" in q:
        return """
    select queue, count(*) as open_count, avg(urgency_score) as avg_urgency
        from support_tickets
    where language = 'en'
      and status <> 'closed'
    group by queue
    order by open_count desc
        limit 15
        """

    if "priority" in q:
        return """
    select priority, status, count(*) as count, avg(urgency_score) as avg_urgency
        from support_tickets
    where language = 'en'
    group by priority, status
    order by count desc
        limit 20
        """

    return """
        select ticket_id, created_at, ticket_type, queue, priority, status, urgency_score, subject
    from support_tickets
        where language = 'en'
    order by urgency_score desc, created_at desc
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
    <title>Support Ticket Analytics</title>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { height: 100%; }
      body { 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; 
        background: #f8f9fa;
        color: #2c3e50;
      }
      .navbar {
        background: white;
        border-bottom: 1px solid #e1e4e8;
        padding: 16px 32px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      }
      .navbar-inner {
        max-width: 1600px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .navbar h1 { font-size: 20px; font-weight: 600; color: #2c3e50; }
      .navbar-sub { font-size: 12px; color: #7f8c8d; margin-top: 4px; }
      .container { max-width: 1600px; margin: 0 auto; padding: 32px; }
      .layout { display: grid; grid-template-columns: 380px 1fr; gap: 32px; }
      @media (max-width: 1200px) { .layout { grid-template-columns: 1fr; } }
      
      .panel {
        background: white;
        border: 1px solid #e1e4e8;
        border-radius: 6px;
        padding: 24px;
      }
      .panel h2 { font-size: 14px; font-weight: 600; color: #2c3e50; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px; }
      
      .form-group { margin-bottom: 16px; }
      label { display: block; font-size: 12px; font-weight: 600; color: #2c3e50; margin-bottom: 6px; }
      textarea {
        width: 100%;
        min-height: 120px;
        padding: 10px;
        border: 1px solid #d0d3d7;
        border-radius: 4px;
        font-family: inherit;
        font-size: 13px;
        resize: vertical;
        transition: border-color 0.15s, box-shadow 0.15s;
      }
      textarea:focus {
        outline: none;
        border-color: #0366d6;
        box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
      }
      
      .btn {
        width: 100%;
        padding: 10px 16px;
        background: #0366d6;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.15s;
      }
      .btn:hover { background: #0256c7; }
      .btn:active { background: #0250b9; }
      
      .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 16px;
      }
      .badge-fallback { background: #ffeaea; color: #cb2431; }
      .badge-alloydb { background: #d3f5d3; color: #238636; }
      
      .sql-display {
        background: #0d1117;
        color: #79c0ff;
        padding: 12px;
        border-radius: 4px;
        border: 1px solid #30363d;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 11px;
        line-height: 1.5;
        overflow-x: auto;
        max-height: 140px;
        margin-bottom: 16px;
      }
      
      .results-section {
        display: none;
      }
      
      .stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 20px;
      }
      .stat {
        background: #f6f8fa;
        border: 1px solid #e1e4e8;
        border-radius: 4px;
        padding: 12px;
        text-align: center;
      }
      .stat-value { font-size: 20px; font-weight: 600; color: #0366d6; }
      .stat-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
      
      .table-container {
        border: 1px solid #e1e4e8;
        border-radius: 4px;
        overflow: hidden;
        max-height: 600px;
        overflow-y: auto;
      }
      
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
      }
      
      thead tr {
        background: #f6f8fa;
        border-bottom: 1px solid #e1e4e8;
      }
      
      th {
        text-align: left;
        font-weight: 600;
        color: #2c3e50;
        padding: 12px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: sticky;
        top: 0;
        background: #f6f8fa;
      }
      
      td {
        padding: 12px;
        border-bottom: 1px solid #e1e4e8;
        color: #444;
      }
      
      tbody tr:hover {
        background: #f6f8fa;
      }
      
      .priority-high { color: #cb2431; font-weight: 600; }
      .priority-medium { color: #b08800; font-weight: 600; }
      .priority-low { color: #238636; font-weight: 600; }
      
      .status-badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 600;
      }
      .status-open { background: #eaeef2; color: #0366d6; }
      .status-pending { background: #fff3cd; color: #997922; }
      .status-closed { background: #dafbe1; color: #238636; }
      
      .empty-state {
        text-align: center;
        padding: 48px 24px;
        color: #666;
      }
      .empty-state p { font-size: 13px; }
      
      .error-banner {
        background: #fff5f7;
        border: 1px solid #ffc8d7;
        border-radius: 4px;
        padding: 12px 16px;
        color: #cb2431;
        font-size: 13px;
        margin-bottom: 24px;
      }
    </style>
  </head>
  <body>
    <div class="navbar">
      <div class="navbar-inner">
        <div>
          <div class="navbar h1">Support Ticket Analytics</div>
          <div class="navbar-sub">Natural Language Query Engine Powered by AlloyDB</div>
        </div>
      </div>
    </div>

    <div class="container">
      <div class="layout">
        <div>
          <div class="panel">
            <h2>Search Tickets</h2>
            <div class="form-group">
              <label>Ask a question about your tickets</label>
              <textarea id="q" placeholder="Examples:&#10;Show incident tickets&#10;Top support categories&#10;Queue analysis&#10;Priority breakdown">Show incident tickets</textarea>
            </div>
            <button class="btn" onclick="runQuery()">Search</button>
            <div id="sqlSection" style="margin-top:20px;display:none;">
              <div class="badge" id="badge"></div>
              <div class="sql-display" id="sql"></div>
            </div>
          </div>
        </div>

        <div id="resultsPanel" class="results-section">
          <div class="panel">
            <h2>Results</h2>
            <div id="errorBanner"></div>
            <div id="stats"></div>
            <div class="table-container">
              <div id="results"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
      async function runQuery() {
        const question = document.getElementById('q').value.trim();
        if (!question) {
          showError('Please enter a question');
          return;
        }

        document.getElementById('resultsPanel').classList.remove('results-section');
        document.getElementById('resultsPanel').style.display = 'none';
        document.getElementById('errorBanner').innerHTML = '';

        try {
          const res = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
          });
          const data = await res.json();

          if (data.error) {
            showError('Error: ' + data.error);
            return;
          }

          // Show SQL
          const badgeClass = data.source === 'alloydb_ai' ? 'badge-alloydb' : 'badge-fallback';
          const badgeText = data.source === 'alloydb_ai' ? 'AlloyDB AI' : 'Pattern Fallback';
          document.getElementById('badge').className = 'badge ' + badgeClass;
          document.getElementById('badge').textContent = badgeText;
          document.getElementById('sql').textContent = data.generated_sql || '';
          document.getElementById('sqlSection').style.display = 'block';

          // Show results
          const rows = data.rows || [];
          if (rows.length === 0) {
            document.getElementById('stats').innerHTML = '';
            document.getElementById('results').innerHTML = '<div class="empty-state"><p>No results found</p></div>';
          } else {
            const keys = Object.keys(rows[0]);
            
            // Stats
            let statsHtml = '<div class="stats"><div class="stat"><div class="stat-value">' + rows.length + '</div><div class="stat-label">Records</div></div>';
            statsHtml += '<div class="stat"><div class="stat-value">' + keys.length + '</div><div class="stat-label">Columns</div></div></div>';
            document.getElementById('stats').innerHTML = statsHtml;

            // Table
            let html = '<table><thead><tr>';
            keys.forEach(k => { html += '<th>' + htmlesc(k) + '</th>'; });
            html += '</tr></thead><tbody>';
            rows.forEach(row => {
              html += '<tr>';
              keys.forEach(k => { 
                let val = String(row[k]);
                let cell = htmlesc(val);
                
                if (k === 'priority') {
                  cell = '<span class="priority-' + val.toLowerCase() + '">' + cell + '</span>';
                }
                if (k === 'status') {
                  cell = '<span class="status-badge status-' + val.toLowerCase() + '">' + cell + '</span>';
                }
                
                html += '<td>' + cell + '</td>'; 
              });
              html += '</tr>';
            });
            html += '</tbody></table>';
            document.getElementById('results').innerHTML = html;
          }
          document.getElementById('resultsPanel').style.display = 'block';
        } catch (err) {
          showError('Network error: ' + err.message);
        }
      }

      function showError(msg) {
        document.getElementById('errorBanner').innerHTML = '<div class="error-banner">' + htmlesc(msg) + '</div>';
        document.getElementById('resultsPanel').style.display = 'block';
      }

      function htmlesc(s) {
        return String(s).replace(/[&<>"']/g, c => ({
          '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
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


# Seed database on startup
try:
    print("Starting database initialization...")
    seed_database()
    print("✓ Database initialization complete")
except Exception as e:
    print(f"⚠ Database initialization failed: {e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
