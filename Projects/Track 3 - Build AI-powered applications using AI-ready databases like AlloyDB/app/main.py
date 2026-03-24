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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
