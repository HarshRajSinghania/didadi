import {describe,it,expect,vi} from 'vitest';
import {createDemo} from './demo-api';
describe('synthetic preview',()=>{
 it('persists snapshots locally, rejects stale saves, and deduplicates retries without network',async()=>{
 const values=new Map(),storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)};
 const fetch=vi.spyOn(globalThis,'fetch').mockRejectedValue(Error('network forbidden'));
 try{const api=createDemo(storage),room=api.session.initialRoom,doc=await api.document(room);
 const content={'m.mentions':{user_ids:[api.session.agentId]},'org.didadi.document':{action:'write',base_blob:doc.blob,content:'# Edited sample'}};
 const result=await api.send(room,content,'same');expect(await api.send(room,content,'same')).toEqual(result);
 expect((await createDemo(storage).document(room)).content).toBe('# Edited sample');expect((await api.history()).commits).toHaveLength(2);
 const stale=await api.send(room,content,'other');expect((await api.task(room,stale.event_id)).task.body).toMatch(/^Document conflict:/);
 expect(fetch).not.toHaveBeenCalled();}finally{fetch.mockRestore()}
 });
});
