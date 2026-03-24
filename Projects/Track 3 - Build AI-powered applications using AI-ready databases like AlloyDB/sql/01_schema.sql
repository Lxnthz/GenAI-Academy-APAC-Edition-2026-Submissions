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
