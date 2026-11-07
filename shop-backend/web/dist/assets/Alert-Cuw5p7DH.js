import{An as e,Bn as t,D as n,In as r,Jn as i,L as a,Mn as o,O as s,On as c,Q as l,V as u,Y as d,Z as f,bt as p,ct as m,et as h,fn as g,ft as _,ht as v,it as y,kn as b,ln as x,on as S,or as C,rt as w,sn as T,un as E,z as D}from"./_plugin-vue_export-helper-Z-C6jLwj.js";import{D as O,E as k,O as A,T as j,k as M}from"./index-DuE9eers.js";var N={iconMargin:`11px 8px 0 12px`,iconMarginRtl:`11px 12px 0 8px`,iconSize:`24px`,closeIconSize:`16px`,closeSize:`20px`,closeMargin:`13px 14px 0 0`,closeMarginRtl:`13px 0 0 14px`,padding:`13px`};function P(e){let{lineHeight:t,borderRadius:n,fontWeightStrong:r,baseColor:i,dividerColor:a,actionColor:o,textColor1:s,textColor2:c,closeColorHover:l,closeColorPressed:u,closeIconColor:d,closeIconColorHover:f,closeIconColorPressed:p,infoColor:m,successColor:h,warningColor:g,errorColor:_,fontSize:v}=e;return{...N,fontSize:v,lineHeight:t,titleFontWeight:r,borderRadius:n,border:`1px solid ${a}`,color:o,titleTextColor:s,iconColor:c,contentTextColor:c,closeBorderRadius:n,closeColorHover:l,closeColorPressed:u,closeIconColor:d,closeIconColorHover:f,closeIconColorPressed:p,borderInfo:`1px solid ${y(i,w(m,{alpha:.25}))}`,colorInfo:y(i,w(m,{alpha:.08})),titleTextColorInfo:s,iconColorInfo:m,contentTextColorInfo:c,closeColorHoverInfo:l,closeColorPressedInfo:u,closeIconColorInfo:d,closeIconColorHoverInfo:f,closeIconColorPressedInfo:p,borderSuccess:`1px solid ${y(i,w(h,{alpha:.25}))}`,colorSuccess:y(i,w(h,{alpha:.08})),titleTextColorSuccess:s,iconColorSuccess:h,contentTextColorSuccess:c,closeColorHoverSuccess:l,closeColorPressedSuccess:u,closeIconColorSuccess:d,closeIconColorHoverSuccess:f,closeIconColorPressedSuccess:p,borderWarning:`1px solid ${y(i,w(g,{alpha:.33}))}`,colorWarning:y(i,w(g,{alpha:.08})),titleTextColorWarning:s,iconColorWarning:g,contentTextColorWarning:c,closeColorHoverWarning:l,closeColorPressedWarning:u,closeIconColorWarning:d,closeIconColorHoverWarning:f,closeIconColorPressedWarning:p,borderError:`1px solid ${y(i,w(_,{alpha:.25}))}`,colorError:y(i,w(_,{alpha:.08})),titleTextColorError:s,iconColorError:_,contentTextColorError:c,closeColorHoverError:l,closeColorPressedError:u,closeIconColorError:d,closeIconColorHoverError:f,closeIconColorPressedError:p}}var F={name:`Alert`,common:h,self:P},I=T(`alert`,`
 line-height: var(--n-line-height);
 border-radius: var(--n-border-radius);
 position: relative;
 transition: background-color .3s var(--n-bezier);
 background-color: var(--n-color);
 text-align: start;
 word-break: break-word;
`,[x(`border`,`
 border-radius: inherit;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 transition: border-color .3s var(--n-bezier);
 border: var(--n-border);
 pointer-events: none;
 `),E(`closable`,[T(`alert-body`,[x(`title`,`
 padding-right: 24px;
 `)])]),x(`icon`,{color:`var(--n-icon-color)`}),T(`alert-body`,{padding:`var(--n-padding)`},[x(`title`,{color:`var(--n-title-text-color)`}),x(`content`,{color:`var(--n-content-text-color)`})]),j({originalTransition:`transform .3s var(--n-bezier)`,enterToProps:{transform:`scale(1)`},leaveToProps:{transform:`scale(0.9)`}}),x(`icon`,`
 position: absolute;
 left: 0;
 top: 0;
 align-items: center;
 justify-content: center;
 display: flex;
 width: var(--n-icon-size);
 height: var(--n-icon-size);
 font-size: var(--n-icon-size);
 margin: var(--n-icon-margin);
 `),x(`close`,`
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 position: absolute;
 right: 0;
 top: 0;
 margin: var(--n-close-margin);
 `),E(`show-icon`,[T(`alert-body`,{paddingLeft:`calc(var(--n-icon-margin-left) + var(--n-icon-size) + var(--n-icon-margin-right))`})]),E(`right-adjust`,[T(`alert-body`,{paddingRight:`calc(var(--n-close-size) + var(--n-padding) + 2px)`})]),T(`alert-body`,`
 border-radius: var(--n-border-radius);
 transition: border-color .3s var(--n-bezier);
 `,[x(`title`,`
 transition: color .3s var(--n-bezier);
 font-size: 16px;
 line-height: 19px;
 font-weight: var(--n-title-font-weight);
 `,[S(`& +`,[x(`content`,{marginTop:`9px`})])]),x(`content`,{transition:`color .3s var(--n-bezier)`,fontSize:`var(--n-font-size)`})]),x(`icon`,{transition:`color .3s var(--n-bezier)`})]),L={...f.props,title:String,showIcon:{type:Boolean,default:!0},type:{type:String,default:`default`},bordered:{type:Boolean,default:!0},closable:Boolean,onClose:Function,onAfterLeave:Function,onAfterHide:Function},R=r({name:`Alert`,inheritAttrs:!1,props:L,slots:Object,setup(e){let{mergedClsPrefixRef:t,mergedBorderedRef:n,inlineThemeDisabled:r,mergedRtlRef:i}=p(e),o=f(`Alert`,`-alert`,I,F,e,t),s=a(`Alert`,i,t),u=c(()=>{let{common:{cubicBezierEaseInOut:t},self:n}=o.value,{fontSize:r,borderRadius:i,titleFontWeight:a,lineHeight:s,iconSize:c,iconMargin:l,iconMarginRtl:u,closeIconSize:d,closeBorderRadius:f,closeSize:p,closeMargin:h,closeMarginRtl:_,padding:v}=n,{type:y}=e,{left:b,right:x}=m(l);return{"--n-bezier":t,"--n-color":n[g(`color`,y)],"--n-close-icon-size":d,"--n-close-border-radius":f,"--n-close-color-hover":n[g(`closeColorHover`,y)],"--n-close-color-pressed":n[g(`closeColorPressed`,y)],"--n-close-icon-color":n[g(`closeIconColor`,y)],"--n-close-icon-color-hover":n[g(`closeIconColorHover`,y)],"--n-close-icon-color-pressed":n[g(`closeIconColorPressed`,y)],"--n-icon-color":n[g(`iconColor`,y)],"--n-border":n[g(`border`,y)],"--n-title-text-color":n[g(`titleTextColor`,y)],"--n-content-text-color":n[g(`contentTextColor`,y)],"--n-line-height":s,"--n-border-radius":i,"--n-font-size":r,"--n-title-font-weight":a,"--n-icon-size":c,"--n-icon-margin":l,"--n-icon-margin-rtl":u,"--n-close-size":p,"--n-close-margin":h,"--n-close-margin-rtl":_,"--n-padding":v,"--n-icon-margin-left":b,"--n-icon-margin-right":x}}),d=r?l(`alert`,c(()=>e.type[0]),u,e):void 0,h=C(!0),_=()=>{let{onAfterLeave:t,onAfterHide:n}=e;t&&t(),n&&n()};return{rtlEnabled:s,mergedClsPrefix:t,mergedBordered:n,visible:h,handleCloseClick:()=>{Promise.resolve(e.onClose?.()).then(e=>{e!==!1&&(h.value=!1)})},handleAfterLeave:()=>{_()},mergedTheme:o,cssVars:r?void 0:u,themeClass:d?.themeClass,onRender:d?.onRender}},render(){return this.onRender?.(),i(),e(n,{onAfterLeave:this.handleAfterLeave},{default:()=>{let{mergedClsPrefix:n,$slots:r}=this,a={class:[`${n}-alert`,this.themeClass,this.closable&&`${n}-alert--closable`,this.showIcon&&`${n}-alert--show-icon`,!this.title&&this.closable&&`${n}-alert--right-adjust`,this.rtlEnabled&&`${n}-alert--rtl`],style:this.cssVars,role:`alert`};return this.visible?(i(),o(`div`,t({key:1},t(this.$attrs,a)),[v(()=>this.closable&&(i(),e(s,{clsPrefix:n,class:_(`${n}-alert__close`),onClick:this.handleCloseClick},null,8,[`clsPrefix`,`class`,`onClick`]))),v(()=>this.bordered&&(i(),o(`div`,{class:_(`${n}-alert__border`)},null,2))),v(()=>this.showIcon&&(i(),o(`div`,{class:_(`${n}-alert__icon`),"aria-hidden":`true`},[v(()=>D(r.icon,()=>[(i(),e(d,{clsPrefix:n},{default:()=>{switch(this.type){case`success`:return i(),e(O,{key:3});case`info`:return i(),e(A,{key:4});case`warning`:return i(),e(k,{key:5});case`error`:return i(),e(M,{key:6});default:return null}}},1032,[`clsPrefix`]))]))],2))),b(`div`,{class:_([`${n}-alert-body`,this.mergedBordered&&`${n}-alert-body--bordered`])},[v(()=>u(r.header,e=>{let t=e||this.title;return t?(i(),o(`div`,{key:2,class:_(`${n}-alert-body__title`)},[v(()=>t)],2)):null})),v(()=>r.default&&(i(),o(`div`,{class:_(`${n}-alert-body__content`)},[v(()=>r.default())],2)))],2)],16)):null}},1032,[`onAfterLeave`])}});export{R as t};