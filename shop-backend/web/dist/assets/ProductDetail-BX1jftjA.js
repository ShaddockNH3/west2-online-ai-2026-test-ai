import{$n as e,An as t,Bn as n,Ct as r,Fn as i,In as a,Jn as o,Kn as s,Mn as c,On as l,Pn as u,Q as d,Rn as f,Xn as p,Yn as m,Z as h,a as g,b as _,bt as v,et as y,fn as b,fr as x,ft as S,ht as C,jn as w,kn as T,ln as E,lr as D,lt as O,m as ee,nt as te,o as k,on as A,or as j,pr as M,qn as N,sn as P,t as ne,tr as F,u as re,un as ie,ur as I,wn as L,z as R,zn as z}from"./_plugin-vue_export-helper-Z-C6jLwj.js";import{A as B,l as V,o as H,s as U,u as W}from"./index-DuE9eers.js";import{t as G}from"./Alert-Cuw5p7DH.js";import{t as K}from"./InputNumber-DbpEhBA0.js";import{t as q}from"./RadioButton-D__bqxM2.js";import{t as J}from"./RadioGroup-BgOceTrK.js";import{n as Y,t as ae}from"./Space-DzmlQzZ7.js";var oe={fontWeightActive:`400`};function se(e){let{fontSize:t,textColor3:n,textColor2:r,borderRadius:i,buttonColor2Hover:a,buttonColor2Pressed:o}=e;return{...oe,fontSize:t,itemLineHeight:`1.25`,itemTextColor:n,itemTextColorHover:r,itemTextColorPressed:r,itemTextColorActive:r,itemBorderRadius:i,itemColorHover:a,itemColorPressed:o,separatorColor:n}}var ce={name:`Breadcrumb`,common:y,self:se},le=P(`breadcrumb`,`
 white-space: nowrap;
 cursor: default;
 line-height: var(--n-item-line-height);
`,[A(`ul`,`
 list-style: none;
 padding: 0;
 margin: 0;
 `),A(`a`,`
 color: inherit;
 text-decoration: inherit;
 `),P(`breadcrumb-item`,`
 font-size: var(--n-font-size);
 transition: color .3s var(--n-bezier);
 display: inline-flex;
 align-items: center;
 `,[P(`icon`,`
 font-size: 18px;
 vertical-align: -.2em;
 transition: color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 `),A(`&:not(:last-child)`,[ie(`clickable`,[E(`link`,`
 cursor: pointer;
 `,[A(`&:hover`,`
 background-color: var(--n-item-color-hover);
 `),A(`&:active`,`
 background-color: var(--n-item-color-pressed); 
 `)])])]),E(`link`,`
 padding: 4px;
 border-radius: var(--n-item-border-radius);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 position: relative;
 `,[A(`&:hover`,`
 color: var(--n-item-text-color-hover);
 `,[P(`icon`,`
 color: var(--n-item-text-color-hover);
 `)]),A(`&:active`,`
 color: var(--n-item-text-color-pressed);
 `,[P(`icon`,`
 color: var(--n-item-text-color-pressed);
 `)])]),E(`separator`,`
 margin: 0 8px;
 color: var(--n-separator-color);
 transition: color .3s var(--n-bezier);
 user-select: none;
 -webkit-user-select: none;
 `),A(`&:last-child`,[E(`link`,`
 font-weight: var(--n-font-weight-active);
 cursor: unset;
 color: var(--n-item-text-color-active);
 `,[P(`icon`,`
 color: var(--n-item-text-color-active);
 `)]),E(`separator`,`
 display: none;
 `)])])]),X=r(`n-breadcrumb`),ue={...h.props,separator:{type:String,default:`/`}},de=a({name:`Breadcrumb`,props:ue,setup(e){let{mergedClsPrefixRef:t,inlineThemeDisabled:n}=v(e),r=h(`Breadcrumb`,`-breadcrumb`,le,ce,e,t);m(X,{separatorRef:D(e,`separator`),mergedClsPrefixRef:t});let i=l(()=>{let{common:{cubicBezierEaseInOut:e},self:{separatorColor:t,itemTextColor:n,itemTextColorHover:i,itemTextColorPressed:a,itemTextColorActive:o,fontSize:s,fontWeightActive:c,itemBorderRadius:l,itemColorHover:u,itemColorPressed:d,itemLineHeight:f}}=r.value;return{"--n-font-size":s,"--n-bezier":e,"--n-item-text-color":n,"--n-item-text-color-hover":i,"--n-item-text-color-pressed":a,"--n-item-text-color-active":o,"--n-separator-color":t,"--n-item-color-hover":u,"--n-item-color-pressed":d,"--n-item-border-radius":l,"--n-font-weight-active":c,"--n-item-line-height":f}}),a=n?d(`breadcrumb`,void 0,i,e):void 0;return{mergedClsPrefix:t,cssVars:n?void 0:i,themeClass:a?.themeClass,onRender:a?.onRender}},render(){return this.onRender?.(),o(),c(`nav`,{class:S([`${this.mergedClsPrefix}-breadcrumb`,this.themeClass]),style:x(this.cssVars),"aria-label":`Breadcrumb`},[T(`ul`,null,[C(()=>this.$slots.default?.())])],6)}});function fe(e=_?window:null){let t=()=>{let{hash:t,host:n,hostname:r,href:i,origin:a,pathname:o,port:s,protocol:c,search:l}=e?.location||{};return{hash:t,host:n,hostname:r,href:i,origin:a,pathname:o,port:s,protocol:c,search:l}},n=j(t()),r=()=>{n.value=t()};return s(()=>{e&&(e.addEventListener(`popstate`,r),e.addEventListener(`hashchange`,r))}),N(()=>{e&&(e.removeEventListener(`popstate`,r),e.removeEventListener(`hashchange`,r))}),n}var Z=a({name:`BreadcrumbItem`,props:{separator:String,href:String,clickable:{type:Boolean,default:!0},showSeparator:{type:Boolean,default:!0},onClick:Function},slots:Object,setup(e,{slots:t}){let n=z(X,null);if(!n)return()=>null;let{separatorRef:r,mergedClsPrefixRef:i}=n,a=fe(),s=l(()=>e.href?`a`:`span`),u=l(()=>a.value.href===e.href?`location`:null);return()=>{let{value:n}=i;return o(),c(`li`,{class:S([`${n}-breadcrumb-item`,e.clickable&&`${n}-breadcrumb-item--clickable`])},[C(()=>f(s.value,{class:`${n}-breadcrumb-item__link`,"aria-current":u.value,href:e.href,onClick:e.onClick},t)),C(()=>e.showSeparator&&(o(),c(`span`,{class:S(`${n}-breadcrumb-item__separator`),"aria-hidden":`true`},[C(()=>R(t.separator,()=>[e.separator??r.value]))],2)))],2)}}}),Q=!1;function pe(){if(_&&window.CSS&&!Q&&(Q=!0,`registerProperty`in window?.CSS))try{CSS.registerProperty({name:`--n-color-start`,syntax:`<color>`,inherits:!1,initialValue:`#0000`}),CSS.registerProperty({name:`--n-color-end`,syntax:`<color>`,inherits:!1,initialValue:`#0000`})}catch{}}function me(e){let{heightSmall:t,heightMedium:n,heightLarge:r,borderRadius:i}=e;return{color:`#eee`,colorEnd:`#ddd`,borderRadius:i,heightSmall:t,heightMedium:n,heightLarge:r}}var he={name:`Skeleton`,common:y,self:me},ge=A([P(`skeleton`,`
 height: 1em;
 width: 100%;
 transition:
 --n-color-start .3s var(--n-bezier),
 --n-color-end .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 animation: 2s skeleton-loading infinite cubic-bezier(0.36, 0, 0.64, 1);
 background-color: var(--n-color-start);
 `),A(`@keyframes skeleton-loading`,`
 0% {
 background: var(--n-color-start);
 }
 40% {
 background: var(--n-color-end);
 }
 80% {
 background: var(--n-color-start);
 }
 100% {
 background: var(--n-color-start);
 }
 `)]),_e={...h.props,text:Boolean,round:Boolean,circle:Boolean,height:[String,Number],width:[String,Number],size:String,repeat:{type:Number,default:1},animated:{type:Boolean,default:!0},sharp:{type:Boolean,default:!0}},ve=a({name:`Skeleton`,inheritAttrs:!1,props:_e,setup(e){pe();let{mergedClsPrefixRef:t,mergedComponentPropsRef:n}=v(e),r=l(()=>e.size||n?.value?.Skeleton?.size),i=h(`Skeleton`,`-skeleton`,ge,he,e,t);return{mergedClsPrefix:t,style:l(()=>{let t=i.value,{common:{cubicBezierEaseInOut:n}}=t,a=t.self,{color:o,colorEnd:s,borderRadius:c}=a,l,{circle:u,sharp:d,round:f,width:p,height:m,text:h,animated:g}=e,_=r.value;_!==void 0&&(l=a[b(`height`,_)]);let v=u?p??m??l:p,y=(u?p??m:m)??l;return{display:h?`inline-block`:``,verticalAlign:h?`-0.125em`:``,borderRadius:u?`50%`:f?`4096px`:d?``:c,width:typeof v==`number`?O(v):v,height:typeof y==`number`?O(y):y,animation:g?``:`none`,"--n-bezier":n,"--n-color-start":o,"--n-color-end":s}})}},render(){let{repeat:e,style:t,mergedClsPrefix:r,$attrs:i}=this,a=f(`div`,n({class:`${r}-skeleton`,style:t},i));return e>1?(o(),c(L,{key:1},[C(()=>te(e,null).map(e=>[a,`
`]))],64)):a}}),ye={class:`page`},be={key:1,class:`detail`},xe={class:`visual`},Se={class:`thumb big`},Ce={class:`row-between`},we={class:`name`},Te={class:`desc`},Ee={class:`muted cat`},De={class:`block`},$={class:`sku-price`},Oe={class:`block`},ke={class:`muted stock-note`},Ae={class:`buy`},je={class:`price-line`},Me={class:`price big-price`},Ne={key:0,class:`muted original`},Pe=ne({__name:`ProductDetail`,setup(n){let r=V(),a=W(),d=Y(),f=j(!0),m=j(null),h=j(null),_=j(1),v=j(!1),y=l(()=>m.value?.skus.find(e=>e.id===h.value)||null);function b(e){let t=Object.values(e||{});return t.length?t.join(` / `):`默认规格`}async function x(){f.value=!0;try{m.value=await g.get(`/products/${r.params.id}`);let e=m.value.skus.find(e=>e.purchasable);h.value=(e||m.value.skus[0])?.id||null}catch(e){d.error(e.message),a.push(`/`)}finally{f.value=!1}}e(h,()=>{_.value=1});async function S(){if(y.value){if(!U.user)a.push({name:`login`,query:{redirect:r.fullPath}});else{v.value=!0;try{await g.post(`/cart/items`,{skuId:y.value.id,quantity:_.value}),await H(),d.success(`已加入购物车`)}catch(e){d.error(e.message)}finally{v.value=!1}}}}return s(x),(e,n)=>(o(),c(`div`,ye,[i(I(de),{class:`crumb`},{default:F(()=>[i(I(Z),{onClick:n[0]||=e=>I(a).push(`/`)},{default:F(()=>[...n[3]||=[u(`全部商品`,-1)]]),_:1}),m.value?(o(),t(I(Z),{key:0},{default:F(()=>[u(M(m.value.category?.name),1)]),_:1})):w(``,!0),m.value?(o(),t(I(Z),{key:1},{default:F(()=>[u(M(m.value.name),1)]),_:1})):w(``,!0)]),_:1}),f.value?(o(),t(I(ve),{key:0,height:`360px`,sharp:!1})):m.value?(o(),c(`div`,be,[T(`div`,xe,[T(`div`,Se,M(m.value.name.slice(0,1)),1),n[4]||=T(`div`,{class:`visual-note muted`},`示意图，实物以工作室群公告为准`,-1)]),i(I(re),{class:`info`},{default:F(()=>[T(`div`,Ce,[T(`h1`,we,M(m.value.name),1),m.value.status===`ON_SALE`?(o(),t(I(B),{key:0,type:`success`,bordered:!1},{default:F(()=>[...n[5]||=[u(`在售`,-1)]]),_:1})):w(``,!0)]),T(`p`,Te,M(m.value.description||`暂无介绍`),1),T(`div`,Ee,M(m.value.category?.name),1),y.value?.activityName?(o(),t(I(G),{key:0,type:`error`,"show-icon":!1,class:`activity`},{default:F(()=>[u(` 正在参加「`+M(y.value.activityName)+`」，活动价 `+M(I(k)(y.value.price))+`， 原价 `+M(I(k)(y.value.originalPrice))+`。 `,1)]),_:1})):w(``,!0),T(`div`,De,[n[6]||=T(`div`,{class:`block-label`},`选择规格`,-1),i(I(J),{value:h.value,"onUpdate:value":n[1]||=e=>h.value=e},{default:F(()=>[i(I(ae),null,{default:F(()=>[(o(!0),c(L,null,p(m.value.skus,e=>(o(),t(I(q),{key:e.id,value:e.id,disabled:!e.purchasable},{default:F(()=>[u(M(b(e.specs))+` `,1),T(`span`,$,M(I(k)(e.price)),1)]),_:2},1032,[`value`,`disabled`]))),128))]),_:1})]),_:1},8,[`value`])]),T(`div`,Oe,[n[7]||=T(`div`,{class:`block-label`},`数量`,-1),i(I(K),{value:_.value,"onUpdate:value":n[2]||=e=>_.value=e,min:1,max:y.value?.availableStock||1,style:{width:`170px`}},null,8,[`value`,`max`]),T(`span`,ke,` 可售 `+M(y.value?.availableStock??0)+` 件 `,1)]),T(`div`,Ae,[T(`div`,je,[T(`span`,Me,M(I(k)(y.value?.price)),1),y.value?.activityName?(o(),c(`span`,Ne,` 原价 `+M(I(k)(y.value?.originalPrice)),1)):w(``,!0)]),i(I(ee),{type:`primary`,size:`large`,loading:v.value,disabled:!y.value?.purchasable,onClick:S},{default:F(()=>[...n[8]||=[u(` 加入购物车 `,-1)]]),_:1},8,[`loading`,`disabled`])])]),_:1})])):w(``,!0)]))}},[[`__scopeId`,`data-v-d9fc024a`]]);export{Pe as default};