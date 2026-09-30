"""Build a local full-video engineering review page; no automatic quality scores."""
import argparse
import hashlib
import html
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--project',type=Path,default=Path('.'))
p.add_argument('--directory',type=Path,default=Path('reports/private/r3'))
a=p.parse_args();root=a.project.resolve();out=a.directory.resolve()
receipts={mode:json.loads((root/f'reports/f1_smoke_r3_{mode}.json').read_text()) for mode in ['native','worldcache']}
prompts={r['name']:r['prompt'] for r in [json.loads(x) for x in (root/'configs/smoke.jsonl').read_text().splitlines()]}
names=receipts['native']['expected_samples'];sections=[];sources=[]
for i,name in enumerate(names):
    label='av' if name.startswith('av') else 'common' if name.startswith('common') else 'physics' if name.startswith('physics') else 'robot'
    videos=[]
    for mode,r in receipts.items():
        samples={x['name']:x for x in r['samples']}
        if name not in samples:
            assert name in {x['name'] for x in r['rejections']}
            videos.append(f'<div><h3>{mode}</h3><p>输出被拒绝，无可审查视频。保留该结果，不计作质量得分。</p></div>')
            continue
        video=out/f'{mode}-{label}.mp4'
        assert hashlib.sha256(video.read_bytes()).hexdigest()==samples[name]['sha256'],str(video)
        sources.append({'case':name,'mode':mode,'file':video.name,'sha256':samples[name]['sha256']})
        videos.append(f'<div><h3>{mode}</h3><video controls playsinline preload="metadata" src="{video.name}"></video></div>')
    sections.append(f'''<section data-name="{html.escape(name,quote=True)}"><h2>{i+1}. {html.escape(label)}</h2>
    <details><summary>查看原始生成要求</summary><p>{html.escape(prompts[name])}</p></details>
    <div class="pair">{''.join(videos)}</div>
    <button class="play">同时从头播放</button><button class="pause">全部暂停</button>
    <p><label><input type="checkbox" class="watched">我已完整观看本场景所有可用视频</label></p>
    <label>语义与动作是否完成<textarea data-field="action" placeholder="分别记录 Native / WorldCache，无法判断时写不确定"></textarea></label>
    <label>运动、接触与可见伪影<textarea data-field="motion_artifacts" placeholder="关注停滞、动作幅度变化、闪烁、拖影、模糊、物体交互"></textarea></label>
    <label>总体观察<select data-field="comparison"><option value="">尚未评价</option><option>WC明显退化</option><option>未见明显差异</option><option>WC明显改善</option><option>不确定或无法配对</option></select></label></section>''')
data={'run':'f1-smoke-r3','review_type':'NONBLIND_ENGINEERING_FULL_VIDEO_REVIEW','sources':sources}
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>F1 r3 完整视频工程审查</title><style>body{max-width:1150px;margin:32px auto;padding:0 20px;background:#f4f6fa;color:#172033;font:16px/1.6 system-ui}section{background:white;padding:24px;margin:24px 0;border-radius:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}video{width:100%;background:#111}textarea{box-sizing:border-box;display:block;width:100%;height:80px;margin:8px 0 16px}button,select{padding:8px;margin:8px 12px 8px 0}details p{font-size:14px}input[type=text]{padding:8px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>
<h1>F1 r3 完整视频工程审查</h1><p>非盲、小样本技术检查。请完整播放后记录；更平滑可能来自运动减少或模糊。过滤通过、解码成功与物理正确是不同判断。此页不会自动评分，也不会自动保存，请结束前导出记录。</p>
<label>审查者 <input type="text" id="reviewer" placeholder="姓名或标识"></label>
'''+''.join(sections)+'''<button id="export">导出审查记录 JSON</button><p id="status"></p><script>
const provenance=PROVENANCE;
document.querySelectorAll('section').forEach(section=>{
 const videos=[...section.querySelectorAll('video')];
 section.querySelector('.play').onclick=()=>videos.forEach(v=>{v.currentTime=0;v.play().catch(()=>{document.querySelector('#status').textContent='请点击各视频的播放按钮。'});});
 section.querySelector('.pause').onclick=()=>videos.forEach(v=>v.pause());
});
document.querySelector('#export').onclick=()=>{
 const reviewer=document.querySelector('#reviewer').value.trim();
 if(!reviewer){document.querySelector('#status').textContent='请填写审查者标识。';return;}
 const reviews=[...document.querySelectorAll('section')].map(s=>({case:s.dataset.name,full_watch_attested:s.querySelector('.watched').checked,...Object.fromEntries([...s.querySelectorAll('[data-field]')].map(x=>[x.dataset.field,x.value]))}));
 const result={...provenance,reviewer,created_at:new Date().toISOString(),status:reviews.every(r=>r.full_watch_attested&&r.comparison)?'REVIEW_RECORDED_REQUIRES_CHECK':'INCOMPLETE',reviews};
 const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='f1-r3-full-video-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);
 document.querySelector('#status').textContent='已导出。评价仅代表本次工程审查，不代表统计结论。';
};</script></html>'''
page=page.replace('PROVENANCE',json.dumps(data,ensure_ascii=False).replace('<','\\u003c'))
(out/'review.html').write_text(page)
print(out/'review.html')
