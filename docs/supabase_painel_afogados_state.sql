-- Estrutura isolada para o estado do Painel Comercial Afogados.
-- O segredo nunca é armazenado: a política contém somente seu SHA-256.
create table if not exists public.painel_afogados_state (
  state_key text primary key,
  payload jsonb not null,
  updated_at timestamptz not null default now(),
  constraint painel_afogados_state_key_check check (state_key = 'current'),
  constraint painel_afogados_state_payload_check check (
    jsonb_typeof(payload) = 'object'
    and payload ? 'config'
    and payload ? 'vendas'
    and payload ? 'historico_importacoes'
  )
);

comment on table public.painel_afogados_state is
  'Estado persistente e isolado do Painel Comercial Afogados (Streamlit).';

alter table public.painel_afogados_state enable row level security;
revoke all on table public.painel_afogados_state from anon, authenticated;
grant select, insert, update on table public.painel_afogados_state to anon;

drop policy if exists painel_afogados_state_select on public.painel_afogados_state;
create policy painel_afogados_state_select
on public.painel_afogados_state for select to anon
using (
  encode(extensions.digest(coalesce((coalesce(nullif(current_setting('request.headers', true), ''), '{}')::jsonb ->> 'x-panel-key'), ''), 'sha256'), 'hex')
  = '769bd777b1b9f141eefde8362c8bffe1a85e3bec94a0c2bb865b66c93fd50ff3'
);

drop policy if exists painel_afogados_state_insert on public.painel_afogados_state;
create policy painel_afogados_state_insert
on public.painel_afogados_state for insert to anon
with check (
  state_key = 'current'
  and encode(extensions.digest(coalesce((coalesce(nullif(current_setting('request.headers', true), ''), '{}')::jsonb ->> 'x-panel-key'), ''), 'sha256'), 'hex')
      = '769bd777b1b9f141eefde8362c8bffe1a85e3bec94a0c2bb865b66c93fd50ff3'
);

drop policy if exists painel_afogados_state_update on public.painel_afogados_state;
create policy painel_afogados_state_update
on public.painel_afogados_state for update to anon
using (
  encode(extensions.digest(coalesce((coalesce(nullif(current_setting('request.headers', true), ''), '{}')::jsonb ->> 'x-panel-key'), ''), 'sha256'), 'hex')
  = '769bd777b1b9f141eefde8362c8bffe1a85e3bec94a0c2bb865b66c93fd50ff3'
)
with check (
  state_key = 'current'
  and encode(extensions.digest(coalesce((coalesce(nullif(current_setting('request.headers', true), ''), '{}')::jsonb ->> 'x-panel-key'), ''), 'sha256'), 'hex')
      = '769bd777b1b9f141eefde8362c8bffe1a85e3bec94a0c2bb865b66c93fd50ff3'
);
