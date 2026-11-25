const BASE=import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1';
export function getToken(){return localStorage.getItem('av_token')}
export async function api<T=any>(path:string,options:RequestInit={}):Promise<T>{const h=new Headers(options.headers||{});if(!(options.body instanceof FormData))h.set('Content-Type','application/json');if(getToken())h.set('Authorization',`Bearer ${getToken()}`);const r=await fetch(BASE+path,{...options,headers:h});const b=await r.json().catch(()=>({}));if(!r.ok)throw new Error(b.detail||'Request failed');return b}
