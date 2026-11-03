import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
const root=resolve(import.meta.dirname,process.argv.includes('--dist')?'dist':'.');
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml'};
http.createServer(async(req,res)=>{try{const path=resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(path!==root&&!path.startsWith(root+sep)){res.writeHead(403).end();return;}const file=path===root?resolve(root,'index.html'):path;if(!['.html','.css','.js','.svg'].includes(extname(file))){res.writeHead(404).end();return;}const data=await readFile(file);res.writeHead(200,{'Content-Type':types[extname(file)],'X-Content-Type-Options':'nosniff'}).end(data);}catch{res.writeHead(404).end('Não encontrado');}}).listen(Number(process.env.PORT)||3000,'0.0.0.0',()=>console.log('Ecos de Teyvat — porta '+(process.env.PORT||3000)));
