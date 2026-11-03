import {publicCloudConfig} from './lib/cloud-config.js';
import {mkdir,copyFile,readdir,rm,writeFile,cp} from 'node:fs/promises';
import {join} from 'node:path';
const config=publicCloudConfig(process.env);
const root=import.meta.dirname;
await rm(join(root,'dist'),{recursive:true,force:true});
await mkdir(join(root,'dist','src'),{recursive:true});
await copyFile(join(root,'index.html'),join(root,'dist','index.html'));
for(const file of await readdir(join(root,'src'))){if(/\.(js|css)$/.test(file))await copyFile(join(root,'src',file),join(root,'dist','src',file));}
console.log('Site estático preparado em dist/.');

await writeFile(join(root,'dist','src','cloud-config.js'),'export const cloudConfig = '+JSON.stringify(config)+';\n');

await cp(join(root,'assets'),join(root,'dist','assets'),{recursive:true});

await cp(join(root,'supabase'),join(root,'dist','supabase'),{recursive:true});
