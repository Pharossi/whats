import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const dir='outputs/pesquisa_whatsapp';
const leads=JSON.parse(await fs.readFile(`${dir}/resultados.json`,'utf8'));
const identity=JSON.parse(await fs.readFile(`${dir}/identidade_fontes.json`,'utf8'));
const digits=v=>String(v??'').replace(/\D/g,'');
const normalize=v=>{let n=digits(v); if([10,11].includes(n.length)) n='55'+n; return [12,13].includes(n.length)&&n.startsWith('55')?n:'';};
const display=n=>n?`+55 (${n.slice(2,4)}) ${n.slice(4,-4)}-${n.slice(-4)}`:'';
const counts=new Map();
for(const l of leads) for(const n of new Set(l.pesquisa.hits.map(h=>h.numero))) {const v=counts.get(n)||new Set();v.add(digits(l.cnpj));counts.set(n,v);}
const body=[],evidence=[];
for(const l of leads){
 const hits=l.pesquisa.hits;
 const nums=[...new Set(hits.map(h=>h.numero))];
 const verified=hits.filter(h=>identity[h.fonte]?.cnpjs?.includes(digits(l.cnpj)));
 const matched=hits.filter(h=>[normalize(l.telefone_maps),normalize(l.telefone_receita),normalize(l.whatsapp_original)].includes(h.numero));
 const confirmed=[...new Set(verified.map(h=>h.numero))];
 let candidate=confirmed.length===1?confirmed[0]:nums.length===1?nums[0]:'';
 let conf=confirmed.length?'Alta — CNPJ na página':matched.length?'Média — coincide com telefone da base':nums.length?'Média — link explícito; vínculo pendente':'Não avaliada';
 let status=nums.length?(confirmed.length?'CNPJ localizado na fonte':'Revisar vínculo com empresa'):l.pesquisa.status;
 if(nums.length>1)status+='; múltiplos números';
 if(nums.some(n=>(counts.get(n)?.size||0)>1))status+='; número compartilhado';
 const source=hits.find(h=>h.numero===candidate)?.fonte||'';
 body.push([l.linha,l.cnpj,l.empresa,l.cidade,l.score,l.whatsapp_original||'',display(candidate),nums.map(display).join(' / '),conf,status,source,'2026-10-27',l.site||'',l.telefone_maps||'',l.telefone_receita||'',l.email||'',l.status_ligacao||'',l.endereco||'',l.pesquisa.paginas.join(' | '),l.pesquisa.erro||'', 'Não avaliada',candidate]);
 for(const h of hits){const id=identity[h.fonte]||{};evidence.push([l.linha,l.cnpj,l.empresa,l.cidade,display(h.numero),h.fonte,h.evidencia,id.titulo||'',(id.cnpjs||[]).join(' / '),id.cnpjs?.includes(digits(l.cnpj))?'CNPJ exato na página':'Vínculo pendente',counts.get(h.numero)?.size||1,'2026-10-27',h.numero]);}
}
const wb=Workbook.create();
const main=wb.worksheets.add('WhatsApp Curitiba e RMC');
const ev=wb.worksheets.add('Evidências');
const headers=['Linha na base original','CNPJ','Razão social','Cidade','Score original','WhatsApp original','WhatsApp pesquisado','Números encontrados','Confiança e vínculo','Resultado da pesquisa','Fonte do número selecionado','Data da consulta','Site da base','Telefone Maps original','Telefone Receita original','E-mail original','Status ligação original','Endereço original','Páginas consultadas','Falha na consulta','Permissão para contato','Número normalizado'];
main.getRange('A2').values=[['Pesquisa de WhatsApp — Curitiba e Região Metropolitana']];
main.getRange('A3').values=[['Consulta em 27/10/2026. Links públicos encontrados não comprovam conta ativa nem permissão para envio.']];
main.getRange('A4').values=[['Registros no recorte']];main.getRange('B4').values=[[leads.length]];
main.getRange('D4').values=[['Com link explícito']];main.getRange('E4').values=[[leads.filter(l=>l.pesquisa.hits.length).length]];
main.getRange('G4').values=[['CNPJ na fonte']];main.getRange('H4').values=[[body.filter(r=>r[8].startsWith('Alta')).length]];
main.getRange('A5').values=[['Sem número não significa ausência de WhatsApp. Pesquisa automática em até 3 páginas por site; sem busca nominal para todos os casos pendentes.']];
main.getRange('A6').values=[['Recorte: 29 municípios da RMC — https://www.amep.pr.gov.br/Pagina/Sobre-RM-de-Curitiba. Números sem +, com país 55.']];
main.getRange('A7:V7').values=[headers];
main.getRange(`A8:V${body.length+7}`).values=body;
main.tables.add(`A7:V${body.length+7}`,true,'PesquisaWhatsApp');
ev.getRange('A1:M1').values=[['Linha na base original','CNPJ','Razão social','Cidade','WhatsApp comercial','Página fonte','Link publicado','Título da página','CNPJs publicados','Verificação do vínculo','CNPJs da base com o número','Data da consulta','Número normalizado']];
if(evidence.length){ev.getRange(`A2:M${evidence.length+1}`).values=evidence;ev.tables.add(`A1:M${evidence.length+1}`,true,'EvidenciasWhatsApp');}
for(const s of [main,ev]){
 s.showGridLines=false;s.tabColor='#253D5B';
 s.getUsedRange().format.font={name:'Arial',size:10,color:'#1F2937'};
 s.getUsedRange().format.verticalAlignment='center';
 s.getUsedRange().format.rowHeight=30;
 s.freezePanes.freezeRows(s===main?7:1);
}
main.getRange('A2').format.font={name:'Arial',size:15,bold:true};
for(const r of ['A3:U3','A5:U5','A6:U6']) main.getRange(r).format.rowHeight=21;
main.getRange('A7:V7').format={fill:'#253D5B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:42,horizontalAlignment:'center'};
ev.getRange('A1:M1').format={fill:'#253D5B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:42,horizontalAlignment:'center'};
const widths=[12,23,55,26,12,23,28,38,43,58,54,18,36,24,24,40,25,55,60,48,24,23];
widths.forEach((width,i)=>main.getRangeByIndexes(6,i,body.length+1,1).format.columnWidth=width);
[12,23,55,26,28,60,70,55,40,30,24,18,23].forEach((width,i)=>ev.getRangeByIndexes(0,i,evidence.length+1,1).format.columnWidth=width);
ev.getRange(`C2:D${evidence.length+1}`).format.wrapText=true;
main.getRange(`C8:D${body.length+7}`).format.wrapText=true;
main.getRange(`I8:J${body.length+7}`).format.wrapText=true;
main.getRange(`B8:B${body.length+7}`).setNumberFormat('@');
main.getRange(`F8:H${body.length+7}`).setNumberFormat('@');
ev.getRange(`E2:E${evidence.length+1}`).setNumberFormat('@');
main.getRange(`I8:I${body.length+7}`).conditionalFormats.add('containsText',{text:'Alta',format:{fill:'#E2EFDA',font:{color:'#24582E'}}});
main.getRange(`J8:J${body.length+7}`).conditionalFormats.add('containsText',{text:'Revisar',format:{fill:'#FFF2CC'}});
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'\'WhatsApp Curitiba e RMC\'!A7:K12',tableMaxRows:6,tableMaxCols:11,maxChars:3500})).ndjson);
await fs.writeFile(`${dir}/preview_base.png`,new Uint8Array(await (await wb.render({sheetName:main.name,range:'A7:D15',scale:1.5,format:'png'})).arrayBuffer()));
await fs.writeFile(`${dir}/preview_evidencias.png`,new Uint8Array(await (await wb.render({sheetName:ev.name,range:'A1:E8',scale:1.5,format:'png'})).arrayBuffer()));
await fs.writeFile(`${dir}/preview_contatos.png`,new Uint8Array(await (await wb.render({sheetName:main.name,range:'G7:J12',scale:1.5,format:'png'})).arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(`${dir}/WhatsApp_Curitiba_RMC.xlsx`);
console.log(JSON.stringify({registros:leads.length,com_links:leads.filter(l=>l.pesquisa.hits.length).length,cnpj_confirmado:body.filter(r=>r[8].startsWith('Alta')).length,evidencias:evidence.length,numeros_unicos:counts.size}));
