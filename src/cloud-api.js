const SESSION_KEY='ecos-cloud-session-v1';
export class CampaignCloud {
  constructor(config,{fetcher=globalThis.fetch.bind(globalThis),storage=globalThis.sessionStorage}={}) {
    this.config=config;this.fetcher=fetcher;this.storage=storage;this.session=null;this.refreshing=null;
    try{const s=JSON.parse(storage.getItem(SESSION_KEY)||'null');if(s?.access_token&&s?.refresh_token&&s?.user?.id)this.session=s;}catch{}
  }
  get configured(){return Boolean(this.config.url&&this.config.key);}
  get user(){return this.session?.user||null;}
  setSession(s){this.session=s?{...s,expires_at:s.expires_at||Math.floor(Date.now()/1000)+(s.expires_in||3600)}:null;try{if(this.session)this.storage.setItem(SESSION_KEY,JSON.stringify(this.session));else this.storage.removeItem(SESSION_KEY);}catch{}}
  async request(path,{method='GET',body,headers={},auth=true,retry=true}={}) {
    if(!this.configured)throw Error('A sala compartilhada ainda não foi conectada.');
    if(auth){if(!this.session)throw Error('Entre na sua conta.');if((this.session.expires_at||0)<Date.now()/1000+60)await this.refresh();}
    const opts={method,headers:{apikey:this.config.key,...(auth?{Authorization:'Bearer '+this.session.access_token}:{}),...headers},signal:AbortSignal.timeout(25000)};
    if(body!==undefined){if(body instanceof Blob)opts.body=body;else{opts.body=JSON.stringify(body);opts.headers['Content-Type']='application/json';}}
    let r;try{r=await this.fetcher(this.config.url+path,opts);}catch{throw Error('Não foi possível conectar. Verifique a internet e tente novamente.');}
    if(r.status===401&&auth&&retry){await this.refresh();return this.request(path,{method,body,headers,auth,retry:false});}
    const text=await r.text();let data;try{data=text?JSON.parse(text):null;}catch{data=null;}
    if(!r.ok){const message=data?.msg||data?.message||data?.error_description||data?.error;
      if(r.status===401)throw Error('Sua sessão expirou. Entre novamente.');
      if(r.status===403)throw Error('Sua conta não tem permissão para esta ação.');
      const error=Error(typeof message==='string'?message.slice(0,300):'Não foi possível concluir a operação.');error.code=data?.code;error.status=r.status;throw error;}
    return data;
  }
  async refresh(){if(this.refreshing)return this.refreshing;const token=this.session?.refresh_token;if(!token)throw Error('Entre novamente na sua conta.');this.refreshing=(async()=>{try{const s=await this.request('/auth/v1/token?grant_type=refresh_token',{method:'POST',body:{refresh_token:token},auth:false});if(this.session?.refresh_token!==token)throw Error('A sessão foi alterada. Entre novamente.');this.setSession(s);return s;}catch(e){if(this.session?.refresh_token===token)this.setSession(null);throw e;}finally{this.refreshing=null;}})();return this.refreshing;}
  async login(email,password){const s=await this.request('/auth/v1/token?grant_type=password',{method:'POST',body:{email,password},auth:false});if(!s?.user||!s.access_token)throw Error('Resposta de autenticação inválida.');this.setSession(s);return s.user;}
  async signup(email,password,redirect){const s=await this.request('/auth/v1/signup?redirect_to='+encodeURIComponent(redirect),{method:'POST',body:{email,password},auth:false});if(s?.access_token)this.setSession(s);return s;}
  async recover(email,redirect){return this.request('/auth/v1/recover?redirect_to='+encodeURIComponent(redirect),{method:'POST',body:{email},auth:false});}
  async changePassword(password){return this.request('/auth/v1/user',{method:'PUT',body:{password}});}
  async callback(hash){const data=new URLSearchParams(hash.replace(/^#/,''));if(data.get('error_description'))throw Error(data.get('error_description').slice(0,300));if(!data.get('access_token'))return false;
    this.setSession({access_token:data.get('access_token'),refresh_token:data.get('refresh_token'),expires_in:Number(data.get('expires_in'))||3600});
    try{const user=await this.request('/auth/v1/user');this.setSession({...this.session,user});return data.get('type')==='recovery'?'recovery':true;}catch(e){this.setSession(null);throw e;}
  }
  async logout(){const token=this.session?.access_token;this.setSession(null);if(token){const r=await this.fetcher(this.config.url+'/auth/v1/logout',{method:'POST',headers:{apikey:this.config.key,Authorization:'Bearer '+token},signal:AbortSignal.timeout(25000)});if(!r.ok&&r.status!==401)throw Error('Você saiu neste navegador; não foi possível revogar a sessão remota.');}}
  async rooms(){return this.request('/rest/v1/campaign_rooms?select=id,name,gm_id&order=created_at.asc');}
  async members(roomId){return this.request('/rest/v1/campaign_members?room_id=eq.'+encodeURIComponent(roomId)+'&select=user_id,display_name&order=joined_at.asc');}
  async items(roomId){return this.request('/rest/v1/campaign_items?room_id=eq.'+encodeURIComponent(roomId)+'&select=*&order=updated_at.desc');}
  async rpc(name,body){return this.request('/rest/v1/rpc/'+name,{method:'POST',body});}
  async saveItem(item,id){return this.request('/rest/v1/campaign_items'+(id?'?id=eq.'+encodeURIComponent(id):''),{method:id?'PATCH':'POST',body:item,headers:{Prefer:'return=representation'}});}
  async deleteItem(id){return this.request('/rest/v1/campaign_items?id=eq.'+encodeURIComponent(id),{method:'DELETE'});}
  async upload(roomId,file){const ext={'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}[file.type];if(!ext||file.size>15728640)throw Error('Envie PNG, JPG ou WebP de até 15 MB.');const path=roomId+'/'+crypto.randomUUID()+'.'+ext;await this.request('/storage/v1/object/campaign-images/'+path,{method:'POST',body:file,headers:{'Content-Type':file.type,'x-upsert':'false'}});return path;}
  async removeImage(path){return this.request('/storage/v1/object/campaign-images',{method:'DELETE',body:{prefixes:[path]}});}
  async combat(roomId){const rows=await this.request('/rest/v1/campaign_combats?room_id=eq.'+encodeURIComponent(roomId)+'&select=*');return rows?.[0]||null;}
  async tokens(itemId){return this.request('/rest/v1/campaign_tokens?item_id=eq.'+encodeURIComponent(itemId)+'&select=*&order=id.asc');}
  async createToken(token){return this.request('/rest/v1/campaign_tokens',{method:'POST',body:token,headers:{Prefer:'return=representation'}});}
  async moveToken(id,x,y){return this.request('/rest/v1/campaign_tokens?id=eq.'+encodeURIComponent(id),{method:'PATCH',body:{x,y},headers:{Prefer:'return=representation'}});}
  async deleteToken(id){return this.request('/rest/v1/campaign_tokens?id=eq.'+encodeURIComponent(id),{method:'DELETE'});}
  async imageUrl(path){if(!path)return null;const safe=path.split('/').map(encodeURIComponent).join('/');const r=await this.request('/storage/v1/object/sign/campaign-images/'+safe,{method:'POST',body:{expiresIn:60}});const signed=r?.signedURL||r?.signedUrl;if(!signed)throw Error('Não foi possível carregar a imagem.');const url=new URL(signed.startsWith('/object/')?'/storage/v1'+signed:signed,this.config.url);if(url.origin!==new URL(this.config.url).origin)throw Error('Endereço de imagem inválido.');return url.href;}
}
