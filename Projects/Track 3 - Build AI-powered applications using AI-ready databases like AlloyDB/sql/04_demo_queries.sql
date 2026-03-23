-- Query 1
select ticket_id, created_at, ticket_type, queue, priority, status, urgency_score, subject
from support_tickets
where language = 'en'
  and queue = 'Technical Support'
  and ticket_type = 'incident'
  and status <> 'closed'
  and urgency_score >= 70
  and created_at >= now() - interval '30 days'
order by urgency_score desc, created_at desc
limit 50;

-- Query 2
select coalesce(tag_1, 'unknown') as top_tag, count(*) as issue_count
from support_tickets
where language = 'en'
group by coalesce(tag_1, 'unknown')
order by issue_count desc
limit 10;

-- Query 3
select queue, count(*) as urgent_open_count
from support_tickets
where language = 'en'
  and status <> 'closed'
  and urgency_score >= 70
group by queue
order by urgent_open_count desc
limit 10;
