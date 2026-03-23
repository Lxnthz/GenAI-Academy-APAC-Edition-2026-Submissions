-- Optional helper for manual SQL seeding.
-- Primary seed path is scripts/seed_from_csv.py
-- If you want to seed using psql directly, use:
-- \copy support_tickets(subject,body,answer,ticket_type,queue,priority,language,version,tag_1,tag_2,tag_3,tag_4,tag_5,tag_6,tag_7,tag_8)
-- from 'data/it_support_ticket_en.csv' with (format csv, header true)

select count(*) as current_rows from support_tickets;
