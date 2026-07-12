-- =========================================================
-- Support Escalation: Tiered Agent Router
-- Initial schema migration
-- Run this in Supabase SQL editor, or via `supabase db push`
-- =========================================================

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------
-- profiles
-- One row per auth.users row. Role lives here, not on the
-- client, so it can be checked from RLS policies via a JWT
-- claim lookup (see helper function below).
-- ---------------------------------------------------------
create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    email text not null,
    full_name text,
    role text not null default 'user' check (role in ('user', 'admin')),
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------
-- conversations
-- ---------------------------------------------------------
create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles (id) on delete cascade,
    title text not null default 'New Chat',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists conversations_user_id_idx on public.conversations (user_id);
create index if not exists conversations_updated_at_idx on public.conversations (updated_at desc);

-- ---------------------------------------------------------
-- messages
-- role: 'user' | 'assistant'
-- metadata holds the full structured backend result (routing,
-- tier1, tier2, confidence, etc.) so the UI can re-render the
-- technical details panel when a conversation is reloaded.
-- ---------------------------------------------------------
create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations (id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists messages_conversation_id_idx on public.messages (conversation_id);
create index if not exists messages_created_at_idx on public.messages (created_at);

-- ---------------------------------------------------------
-- query_logs
-- Mirrors what logger.py used to write to logs/requests.json,
-- now persisted centrally so the admin dashboard can query it.
-- ---------------------------------------------------------
create table if not exists public.query_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.profiles (id) on delete set null,
    conversation_id uuid references public.conversations (id) on delete set null,
    query text not null,
    retrieval_confidence numeric not null default 0,
    tier_used text not null,
    specialist text default '',
    category text not null default 'General',
    status text not null,
    resolved boolean not null default false,
    resolved_by text,
    escalated boolean not null default false,
    route jsonb not null default '[]'::jsonb,
    response_time_ms integer,
    created_at timestamptz not null default now()
);

create index if not exists query_logs_created_at_idx on public.query_logs (created_at desc);
create index if not exists query_logs_category_idx on public.query_logs (category);
create index if not exists query_logs_user_id_idx on public.query_logs (user_id);

-- =========================================================
-- Helper: is_admin()
-- Reads role straight from public.profiles for the current
-- auth.uid(). Used inside RLS policies below.
-- =========================================================
create or replace function public.is_admin()
returns boolean
language sql
security definer
set search_path = public
as $$
    select exists (
        select 1 from public.profiles
        where id = auth.uid() and role = 'admin'
    );
$$;

-- =========================================================
-- Row Level Security
-- =========================================================
alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.query_logs enable row level security;

-- profiles ---------------------------------------------------
create policy "profiles_select_own_or_admin"
    on public.profiles for select
    using (id = auth.uid() or public.is_admin());

create policy "profiles_update_own"
    on public.profiles for update
    using (id = auth.uid());

create policy "profiles_insert_own"
    on public.profiles for insert
    with check (id = auth.uid());

-- conversations ------------------------------------------------
create policy "conversations_select_own_or_admin"
    on public.conversations for select
    using (user_id = auth.uid() or public.is_admin());

create policy "conversations_insert_own"
    on public.conversations for insert
    with check (user_id = auth.uid());

create policy "conversations_update_own"
    on public.conversations for update
    using (user_id = auth.uid());

create policy "conversations_delete_own"
    on public.conversations for delete
    using (user_id = auth.uid());

-- messages -------------------------------------------------------
-- Ownership is derived through the parent conversation.
create policy "messages_select_own_or_admin"
    on public.messages for select
    using (
        public.is_admin()
        or exists (
            select 1 from public.conversations c
            where c.id = messages.conversation_id and c.user_id = auth.uid()
        )
    );

create policy "messages_insert_own"
    on public.messages for insert
    with check (
        exists (
            select 1 from public.conversations c
            where c.id = messages.conversation_id and c.user_id = auth.uid()
        )
    );

create policy "messages_delete_own"
    on public.messages for delete
    using (
        exists (
            select 1 from public.conversations c
            where c.id = messages.conversation_id and c.user_id = auth.uid()
        )
    );

-- query_logs -------------------------------------------------------
create policy "query_logs_select_own_or_admin"
    on public.query_logs for select
    using (user_id = auth.uid() or public.is_admin());

create policy "query_logs_insert_own"
    on public.query_logs for insert
    with check (user_id = auth.uid());

-- =========================================================
-- Auto-create a profile row whenever a new auth user signs up
-- =========================================================
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, email, full_name, role)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'full_name', ''),
        'user'
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

-- =========================================================
-- Keep conversations.updated_at fresh whenever a message lands
-- =========================================================
create or replace function public.touch_conversation()
returns trigger
language plpgsql
as $$
begin
    update public.conversations
    set updated_at = now()
    where id = new.conversation_id;
    return new;
end;
$$;

drop trigger if exists on_message_insert on public.messages;
create trigger on_message_insert
    after insert on public.messages
    for each row execute procedure public.touch_conversation();

-- =========================================================
-- To promote a user to admin, run manually in the SQL editor:
-- update public.profiles set role = 'admin' where email = 'you@example.com';
-- =========================================================
