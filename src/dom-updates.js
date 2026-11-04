// Keep interactive nodes and decoded images alive across unchanged polling responses.
const htmlCache=new WeakMap();
export function updateHTML(element,html){if(htmlCache.get(element)===html&&(html===''||element.hasChildNodes()))return false;htmlCache.set(element,html);element.innerHTML=html;return true;}
export function updateText(element,text){text=String(text??'');if(element.textContent===text)return false;element.textContent=text;return true;}
export function updateAttribute(element,name,value){value=String(value);if(element.getAttribute(name)!==value)element.setAttribute(name,value);}
const listCache=new WeakMap();
export function updateKeyedHTML(container,entries,emptyHTML){
 let cached=listCache.get(container);if(!cached){cached=new Map();listCache.set(container,cached);container.replaceChildren();}
 const wanted=new Set(entries.map(e=>e.key));for(const [key,entry] of cached)if(!wanted.has(key)){entry.node.remove();cached.delete(key);}
 if(!entries.length){updateHTML(container,emptyHTML);return;}
 if(!cached.size)container.replaceChildren();
 let cursor=container.firstElementChild;
 for(const entry of entries){let previous=cached.get(entry.key);if(!previous||previous.version!==entry.version){const template=document.createElement('template');template.innerHTML=entry.html();const node=template.content.firstElementChild;if(previous){if(cursor===previous.node)cursor=node;previous.node.replaceWith(node);}previous={node,version:entry.version};cached.set(entry.key,previous);}if(previous.node!==cursor)container.insertBefore(previous.node,cursor);cursor=previous.node.nextElementSibling;}
}
