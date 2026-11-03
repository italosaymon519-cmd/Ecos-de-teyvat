export function publicCloudConfig(env) {
  const url = (env.PUBLIC_SUPABASE_URL || '').trim().replace(/\/$/, '');
  const key = (env.PUBLIC_SUPABASE_PUBLISHABLE_KEY || '').trim();
  if (!url && !key) return { url: '', key: '' };
  if (!url || !key) throw new Error('Configure PUBLIC_SUPABASE_URL e PUBLIC_SUPABASE_PUBLISHABLE_KEY juntas.');
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) throw new Error('PUBLIC_SUPABASE_URL deve ser a URL HTTPS do projeto.');
  if (key.startsWith('sb_publishable_')) return { url, key };
  let payload;
  try { payload = JSON.parse(Buffer.from(key.split('.')[1], 'base64url').toString()); } catch { throw new Error('Use somente a chave publishable ou anon pública do Supabase.'); }
  if (payload.role !== 'anon') throw new Error('Chaves secret/service_role nunca podem ser publicadas no navegador.');
  return { url, key };
}
