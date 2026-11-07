import{An as e,F as t,Fn as n,In as r,Jn as i,Mn as a,On as o,Q as s,S as c,Y as l,Z as u,_n as d,bt as f,dt as p,er as m,et as h,fn as g,fr as _,ft as v,ht as y,kn as b,ln as x,lt as S,on as C,or as w,sn as T,un as E,wn as D,x as O}from"./_plugin-vue_export-helper-Z-C6jLwj.js";import{c as k}from"./Space-DzmlQzZ7.js";import{g as A}from"./Popover-D2KS4s02.js";var j={iconSizeTiny:`28px`,iconSizeSmall:`34px`,iconSizeMedium:`40px`,iconSizeLarge:`46px`,iconSizeHuge:`52px`};function M(e){let{textColorDisabled:t,iconColor:n,textColor2:r,fontSizeTiny:i,fontSizeSmall:a,fontSizeMedium:o,fontSizeLarge:s,fontSizeHuge:c}=e;return{...j,fontSizeTiny:i,fontSizeSmall:a,fontSizeMedium:o,fontSizeLarge:s,fontSizeHuge:c,textColor:t,iconColor:n,extraTextColor:r}}var N={name:`Empty`,common:h,self:M},P=r({name:`Empty`,render(){return(()=>{let e=p(`15c1a247ae156450`);return e[0]||=b(`svg`,{viewBox:`0 0 28 28`,fill:`none`,xmlns:`http://www.w3.org/2000/svg`},[b(`path`,{d:`M26 7.5C26 11.0899 23.0899 14 19.5 14C15.9101 14 13 11.0899 13 7.5C13 3.91015 15.9101 1 19.5 1C23.0899 1 26 3.91015 26 7.5ZM16.8536 4.14645C16.6583 3.95118 16.3417 3.95118 16.1464 4.14645C15.9512 4.34171 15.9512 4.65829 16.1464 4.85355L18.7929 7.5L16.1464 10.1464C15.9512 10.3417 15.9512 10.6583 16.1464 10.8536C16.3417 11.0488 16.6583 11.0488 16.8536 10.8536L19.5 8.20711L22.1464 10.8536C22.3417 11.0488 22.6583 11.0488 22.8536 10.8536C23.0488 10.6583 23.0488 10.3417 22.8536 10.1464L20.2071 7.5L22.8536 4.85355C23.0488 4.65829 23.0488 4.34171 22.8536 4.14645C22.6583 3.95118 22.3417 3.95118 22.1464 4.14645L19.5 6.79289L16.8536 4.14645Z`,fill:`currentColor`}),b(`path`,{d:`M25 22.75V12.5991C24.5572 13.0765 24.053 13.4961 23.5 13.8454V16H17.5L17.3982 16.0068C17.0322 16.0565 16.75 16.3703 16.75 16.75C16.75 18.2688 15.5188 19.5 14 19.5C12.4812 19.5 11.25 18.2688 11.25 16.75L11.2432 16.6482C11.1935 16.2822 10.8797 16 10.5 16H4.5V7.25C4.5 6.2835 5.2835 5.5 6.25 5.5H12.2696C12.4146 4.97463 12.6153 4.47237 12.865 4H6.25C4.45507 4 3 5.45507 3 7.25V22.75C3 24.5449 4.45507 26 6.25 26H21.75C23.5449 26 25 24.5449 25 22.75ZM4.5 22.75V17.5H9.81597L9.85751 17.7041C10.2905 19.5919 11.9808 21 14 21L14.215 20.9947C16.2095 20.8953 17.842 19.4209 18.184 17.5H23.5V22.75C23.5 23.7165 22.7165 24.5 21.75 24.5H6.25C5.2835 24.5 4.5 23.7165 4.5 22.75Z`,fill:`currentColor`})],-1)})()}}),F=T(`empty`,`
 display: flex;
 flex-direction: column;
 align-items: center;
 font-size: var(--n-font-size);
`,[x(`icon`,`
 width: var(--n-icon-size);
 height: var(--n-icon-size);
 font-size: var(--n-icon-size);
 line-height: var(--n-icon-size);
 color: var(--n-icon-color);
 transition:
 color .3s var(--n-bezier);
 `,[C(`+`,[x(`description`,`
 margin-top: 8px;
 `)])]),x(`description`,`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),x(`extra`,`
 text-align: center;
 transition: color .3s var(--n-bezier);
 margin-top: 12px;
 color: var(--n-extra-text-color);
 `)]),I={...u.props,description:String,showDescription:{type:Boolean,default:!0},showIcon:{type:Boolean,default:!0},size:{type:String,default:`medium`},renderIcon:Function},L=r({name:`Empty`,props:I,slots:Object,setup(t){let{mergedClsPrefixRef:n,inlineThemeDisabled:r,mergedComponentPropsRef:a}=f(t),c=u(`Empty`,`-empty`,F,N,t,n),{localeRef:l}=k(`Empty`),d=o(()=>t.description??a?.value?.Empty?.description),p=o(()=>a?.value?.Empty?.renderIcon||(()=>(i(),e(P)))),m=o(()=>{let{size:e}=t,{common:{cubicBezierEaseInOut:n},self:{[g(`iconSize`,e)]:r,[g(`fontSize`,e)]:i,textColor:a,iconColor:o,extraTextColor:s}}=c.value;return{"--n-icon-size":r,"--n-font-size":i,"--n-bezier":n,"--n-text-color":a,"--n-icon-color":o,"--n-extra-text-color":s}}),h=r?s(`empty`,o(()=>{let e=``,{size:n}=t;return e+=n[0],e}),m,t):void 0;return{mergedClsPrefix:n,mergedRenderIcon:p,localizedDescription:o(()=>d.value||l.value.description),cssVars:r?void 0:m,themeClass:h?.themeClass,onRender:h?.onRender}},render(){let{$slots:t,mergedClsPrefix:n,onRender:r}=this;return r?.(),i(),a(`div`,{class:v([`${n}-empty`,this.themeClass]),style:_(this.cssVars)},[this.showIcon?(i(),a(`div`,{key:0,class:v(`${n}-empty__icon`)},[t.icon?(i(),a(D,{key:0},[y(()=>t.icon())],64)):(i(),e(l,{key:1,clsPrefix:n},{default:this.mergedRenderIcon},1032,[`clsPrefix`]))],2)):y(()=>null),this.showDescription?(i(),a(`div`,{key:2,class:v(`${n}-empty__description`)},[t.default?(i(),a(D,{key:0},[y(()=>t.default())],64)):(i(),a(D,{key:1},[y(()=>this.localizedDescription)],64))],2)):y(()=>null),t.extra?(i(),a(`div`,{key:4,class:v(`${n}-empty__extra`)},[y(()=>t.extra())],2)):y(()=>null)],6)}});function R(e){let{opacityDisabled:t,heightTiny:n,heightSmall:r,heightMedium:i,heightLarge:a,heightHuge:o,primaryColor:s,fontSize:c}=e;return{fontSize:c,textColor:s,sizeTiny:n,sizeSmall:r,sizeMedium:i,sizeLarge:a,sizeHuge:o,color:s,opacitySpinning:t}}var z={name:`Spin`,common:h,self:R},B=C([C(`@keyframes spin-rotate`,`
 from {
 transform: rotate(0);
 }
 to {
 transform: rotate(360deg);
 }
 `),T(`spin-container`,`
 position: relative;
 `,[T(`spin-body`,`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 `,[t()])]),T(`spin-body`,`
 display: inline-flex;
 align-items: center;
 justify-content: center;
 flex-direction: column;
 `),T(`spin`,`
 display: inline-flex;
 height: var(--n-size);
 width: var(--n-size);
 font-size: var(--n-size);
 color: var(--n-color);
 `,[E(`rotate`,`
 animation: spin-rotate 2s linear infinite;
 `)]),T(`spin-description`,`
 display: inline-block;
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 margin-top: 8px;
 `),T(`spin-content`,`
 opacity: 1;
 transition: opacity .3s var(--n-bezier);
 pointer-events: all;
 `,[E(`spinning`,`
 user-select: none;
 -webkit-user-select: none;
 pointer-events: none;
 opacity: var(--n-opacity-spinning);
 `)])]),V={small:20,medium:18,large:16},H={...u.props,contentClass:String,contentStyle:[Object,String],description:String,size:{type:[String,Number],default:`medium`},show:{type:Boolean,default:!0},rotate:{type:Boolean,default:!0},spinning:{type:Boolean,validator:()=>!0,default:void 0},delay:Number,...c,strokeWidth:Number},U=r({name:`Spin`,props:H,slots:Object,setup(e){let{mergedClsPrefixRef:t,inlineThemeDisabled:n}=f(e),r=u(`Spin`,`-spin`,B,z,e,t),i=o(()=>{let{size:t}=e,{common:{cubicBezierEaseInOut:n},self:i}=r.value,{opacitySpinning:a,color:o,textColor:s}=i;return{"--n-bezier":n,"--n-opacity-spinning":a,"--n-size":typeof t==`number`?S(t):i[g(`size`,t)],"--n-color":o,"--n-text-color":s}}),a=n?s(`spin`,o(()=>{let{size:t}=e;return typeof t==`number`?String(t):t[0]}),i,e):void 0,c=A(e,[`spinning`,`show`]),l=w(!1);return m(t=>{let n;if(c.value){let{delay:r}=e;if(r){n=window.setTimeout(()=>{l.value=!0},r),t(()=>{clearTimeout(n)});return}}l.value=c.value}),{mergedClsPrefix:t,active:l,mergedStrokeWidth:o(()=>{let{strokeWidth:t}=e;if(t!==void 0)return t;let{size:n}=e;return V[typeof n==`number`?`medium`:n]}),cssVars:n?void 0:i,themeClass:a?.themeClass,onRender:a?.onRender}},render(){let{$slots:t,mergedClsPrefix:r,description:o}=this,s=t.icon&&this.rotate,c=(o||t.description)&&(i(),a(`div`,{class:v(`${r}-spin-description`)},[y(()=>o||t.description?.())],2)),l=t.icon?(i(),a(`div`,{key:1,class:v([`${r}-spin-body`,this.themeClass])},[b(`div`,{class:v([`${r}-spin`,s&&`${r}-spin--rotate`]),style:_(t.default?``:this.cssVars)},[y(()=>t.icon())],6),y(()=>c)],2)):(i(),a(`div`,{key:2,class:v([`${r}-spin-body`,this.themeClass])},[(i(),e(O,{clsPrefix:r,style:_(t.default?``:this.cssVars),stroke:this.stroke,"stroke-width":this.mergedStrokeWidth,radius:this.radius,scale:this.scale,class:v(`${r}-spin`)},null,8,[`clsPrefix`,`style`,`stroke`,`stroke-width`,`radius`,`scale`,`class`])),y(()=>c)],2));return this.onRender?.(),t.default?(i(),a(`div`,{key:3,class:v([`${r}-spin-container`,this.themeClass]),style:_(this.cssVars)},[b(`div`,{class:v([`${r}-spin-content`,this.active&&`${r}-spin-content--spinning`,this.contentClass]),style:_(this.contentStyle)},[y(()=>t.default?.())],6),n(d,{name:`fade-in-transition`},{default:()=>this.active?l:null},1024)],6)):l}});export{L as n,N as r,U as t};