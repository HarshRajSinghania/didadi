import {unified} from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
const parser=unified().use(remarkParse).use(remarkGfm);
const supported=new Set(['root','paragraph','heading','list','listItem','blockquote','code','thematicBreak','text','strong','emphasis','delete','inlineCode','link','break']);
export function unsupportedMarkdown(value){
  if(/^---\s*\n[\s\S]*?\n---(?:\n|$)/.test(value))return 'front matter';
  let unsupported=null;
  function visit(node){if(!supported.has(node.type))unsupported ||= node.type;if(node.type==='code'&&node.meta)unsupported ||= 'code block metadata';node.children?.forEach(visit)}
  visit(parser.parse(value));return unsupported;
}
// Source formatting (bullet marker, fences and spacing) can normalize; semantic blocks must survive.
export function semanticMarkdown(value){
  function clean(node){const {position,spread,...rest}=node;return {...rest,...(rest.children?{children:rest.children.map(clean)}:{})}}
  return clean(parser.parse(value));
}
