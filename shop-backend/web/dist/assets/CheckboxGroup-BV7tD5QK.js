import{An as e,C as t,Ct as n,E as r,Fn as i,G as a,In as o,J as s,Jn as c,K as l,L as u,Mn as d,On as f,Q as p,U as m,V as h,Yn as g,Z as _,bt as v,dt as y,et as b,fn as x,fr as S,ft as C,ht as w,kn as T,ln as E,lr as D,mn as O,on as k,or as A,pn as j,rt as M,sn as N,tt as P,un as F,w as I,wn as L,zn as R}from"./_plugin-vue_export-helper-Z-C6jLwj.js";var z={sizeSmall:`14px`,sizeMedium:`16px`,sizeLarge:`18px`,labelPadding:`0 8px`,labelFontWeight:`400`};function B(e){let{baseColor:t,inputColorDisabled:n,cardColor:r,modalColor:i,popoverColor:a,textColorDisabled:o,borderColor:s,primaryColor:c,textColor2:l,fontSizeSmall:u,fontSizeMedium:d,fontSizeLarge:f,borderRadiusSmall:p,lineHeight:m}=e;return{...z,labelLineHeight:m,fontSizeSmall:u,fontSizeMedium:d,fontSizeLarge:f,borderRadius:p,color:t,colorChecked:c,colorDisabled:n,colorDisabledChecked:n,colorTableHeader:r,colorTableHeaderModal:i,colorTableHeaderPopover:a,checkMarkColor:t,checkMarkColorDisabled:o,checkMarkColorDisabledChecked:o,border:`1px solid ${s}`,borderDisabled:`1px solid ${s}`,borderDisabledChecked:`1px solid ${s}`,borderChecked:`1px solid ${c}`,borderFocus:`1px solid ${c}`,boxShadowFocus:`0 0 0 2px ${M(c,{alpha:.3})}`,textColor:l,textColorDisabled:o}}var V={name:`Checkbox`,common:b,self:B},H=()=>(()=>{let e=y(`75be776d8875fa17`);return e[0]||=T(`svg`,{viewBox:`0 0 64 64`,class:`check-icon`},[T(`path`,{d:`M50.42,16.76L22.34,39.45l-8.1-11.46c-1.12-1.58-3.3-1.96-4.88-0.84c-1.58,1.12-1.95,3.3-0.84,4.88l10.26,14.51  c0.56,0.79,1.42,1.31,2.38,1.45c0.16,0.02,0.32,0.03,0.48,0.03c0.8,0,1.57-0.27,2.2-0.78l30.99-25.03c1.5-1.21,1.74-3.42,0.52-4.92  C54.13,15.78,51.93,15.55,50.42,16.76z`})],-1)})(),U=()=>(()=>{let e=y(`c6eed899356c8404`);return e[0]||=T(`svg`,{viewBox:`0 0 100 100`,class:`line-icon`},[T(`path`,{d:`M80.2,55.5H21.4c-2.8,0-5.1-2.5-5.1-5.5l0,0c0-3,2.3-5.5,5.1-5.5h58.7c2.8,0,5.1,2.5,5.1,5.5l0,0C85.2,53.1,82.9,55.5,80.2,55.5z`})],-1)})(),W=k([N(`checkbox`,`
 font-size: var(--n-font-size);
 outline: none;
 cursor: pointer;
 display: inline-flex;
 flex-wrap: nowrap;
 align-items: flex-start;
 word-break: break-word;
 line-height: var(--n-size);
 --n-merged-color-table: var(--n-color-table);
 `,[F(`show-label`,`line-height: var(--n-label-line-height);`),k(`&:hover`,[N(`checkbox-box`,[E(`border`,`border: var(--n-border-checked);`)])]),k(`&:focus:not(:active)`,[N(`checkbox-box`,[E(`border`,`
 border: var(--n-border-focus);
 box-shadow: var(--n-box-shadow-focus);
 `)])]),F(`inside-table`,[N(`checkbox-box`,`
 background-color: var(--n-merged-color-table);
 `)]),F(`checked`,[N(`checkbox-box`,`
 background-color: var(--n-color-checked);
 `,[N(`checkbox-icon`,[k(`.check-icon`,`
 opacity: 1;
 transform: scale(1);
 `)])])]),F(`indeterminate`,[N(`checkbox-box`,[N(`checkbox-icon`,[k(`.check-icon`,`
 opacity: 0;
 transform: scale(.5);
 `),k(`.line-icon`,`
 opacity: 1;
 transform: scale(1);
 `)])])]),F(`checked, indeterminate`,[k(`&:focus:not(:active)`,[N(`checkbox-box`,[E(`border`,`
 border: var(--n-border-checked);
 box-shadow: var(--n-box-shadow-focus);
 `)])]),N(`checkbox-box`,`
 background-color: var(--n-color-checked);
 border-left: 0;
 border-top: 0;
 `,[E(`border`,{border:`var(--n-border-checked)`})])]),F(`disabled`,{cursor:`not-allowed`},[F(`checked`,[N(`checkbox-box`,`
 background-color: var(--n-color-disabled-checked);
 `,[E(`border`,{border:`var(--n-border-disabled-checked)`}),N(`checkbox-icon`,[k(`.check-icon, .line-icon`,{fill:`var(--n-check-mark-color-disabled-checked)`})])])]),N(`checkbox-box`,`
 background-color: var(--n-color-disabled);
 `,[E(`border`,`
 border: var(--n-border-disabled);
 `),N(`checkbox-icon`,[k(`.check-icon, .line-icon`,`
 fill: var(--n-check-mark-color-disabled);
 `)])]),E(`label`,`
 color: var(--n-text-color-disabled);
 `)]),N(`checkbox-box-wrapper`,`
 position: relative;
 width: var(--n-size);
 flex-shrink: 0;
 flex-grow: 0;
 user-select: none;
 -webkit-user-select: none;
 `),N(`checkbox-box`,`
 position: absolute;
 left: 0;
 top: 50%;
 transform: translateY(-50%);
 height: var(--n-size);
 width: var(--n-size);
 display: inline-block;
 box-sizing: border-box;
 border-radius: var(--n-border-radius);
 background-color: var(--n-color);
 transition: background-color 0.3s var(--n-bezier);
 `,[E(`border`,`
 transition:
 border-color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 border-radius: inherit;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border: var(--n-border);
 `),N(`checkbox-icon`,`
 display: flex;
 align-items: center;
 justify-content: center;
 position: absolute;
 left: 1px;
 right: 1px;
 top: 1px;
 bottom: 1px;
 `,[k(`.check-icon, .line-icon`,`
 width: 100%;
 fill: var(--n-check-mark-color);
 opacity: 0;
 transform: scale(0.5);
 transform-origin: center;
 transition:
 fill 0.3s var(--n-bezier),
 transform 0.3s var(--n-bezier),
 opacity 0.3s var(--n-bezier),
 border-color 0.3s var(--n-bezier);
 `),t({left:`1px`,top:`1px`})])]),E(`label`,`
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 user-select: none;
 -webkit-user-select: none;
 padding: var(--n-label-padding);
 font-weight: var(--n-label-font-weight);
 `,[k(`&:empty`,{display:`none`})])]),j(N(`checkbox`,`
 --n-merged-color-table: var(--n-color-table-modal);
 `)),O(N(`checkbox`,`
 --n-merged-color-table: var(--n-color-table-popover);
 `))]),G=[`id`],K=[`tabindex`,`aria-checked`,`aria-labelledby`,`onKeyup`,`onKeydown`,`onClick`],q={..._.props,size:String,checked:{type:[Boolean,String,Number],default:void 0},defaultChecked:{type:[Boolean,String,Number],default:!1},value:[String,Number],disabled:{type:Boolean,default:void 0},indeterminate:Boolean,label:String,focusable:{type:Boolean,default:!0},checkedValue:{type:[Boolean,String,Number],default:!0},uncheckedValue:{type:[Boolean,String,Number],default:!1},"onUpdate:checked":[Function,Array],onUpdateChecked:[Function,Array],privateInsideTable:Boolean,onChange:[Function,Array]},J=o({name:`Checkbox`,props:q,setup(e){let t=R(Y,null),n=A(null),{mergedClsPrefixRef:i,inlineThemeDisabled:o,mergedRtlRef:s,mergedComponentPropsRef:c}=v(e),d=A(e.defaultChecked),h=D(e,`checked`),g=a(h,d),y=l(()=>{if(t){let n=t.valueSetRef.value;return n&&e.value!==void 0?n.has(e.value):!1}return g.value===e.checkedValue}),b=r(e,{mergedSize(n){let{size:r}=e;if(r!==void 0)return r;if(t){let{value:e}=t.mergedSizeRef;if(e!==void 0)return e}if(n){let{mergedSize:e}=n;if(e!==void 0)return e.value}return c?.value?.Checkbox?.size||`medium`},mergedDisabled(n){let{disabled:r}=e;if(r!==void 0)return r;if(t){if(t.disabledRef.value)return!0;let{maxRef:{value:e},checkedCountRef:n}=t;if(e!==void 0&&n.value>=e&&!y.value)return!0;let{minRef:{value:r}}=t;if(r!==void 0&&n.value<=r&&y.value)return!0}return n?n.disabled.value:!1}}),{mergedDisabledRef:S,mergedSizeRef:C}=b,w=_(`Checkbox`,`-checkbox`,W,V,e,i);function T(n){if(t&&e.value!==void 0)t.toggleCheckbox(!y.value,e.value);else{let{onChange:t,"onUpdate:checked":r,onUpdateChecked:i}=e,{nTriggerFormInput:a,nTriggerFormChange:o}=b,s=y.value?e.uncheckedValue:e.checkedValue;r&&m(r,s,n),i&&m(i,s,n),t&&m(t,s,n),a(),o(),d.value=s}}function E(e){S.value||T(e)}function O(e){if(!S.value)switch(e.key){case` `:case`Enter`:T(e)}}function k(e){e.key===` `&&e.preventDefault()}let j={focus:()=>{n.value?.focus()},blur:()=>{n.value?.blur()}},M=u(`Checkbox`,s,i),N=f(()=>{let{value:e}=C,{common:{cubicBezierEaseInOut:t},self:{borderRadius:n,color:r,colorChecked:i,colorDisabled:a,colorTableHeader:o,colorTableHeaderModal:s,colorTableHeaderPopover:c,checkMarkColor:l,checkMarkColorDisabled:u,border:d,borderFocus:f,borderDisabled:p,borderChecked:m,boxShadowFocus:h,textColor:g,textColorDisabled:_,checkMarkColorDisabledChecked:v,colorDisabledChecked:y,borderDisabledChecked:b,labelPadding:S,labelLineHeight:T,labelFontWeight:E,[x(`fontSize`,e)]:D,[x(`size`,e)]:O}}=w.value;return{"--n-label-line-height":T,"--n-label-font-weight":E,"--n-size":O,"--n-bezier":t,"--n-border-radius":n,"--n-border":d,"--n-border-checked":m,"--n-border-focus":f,"--n-border-disabled":p,"--n-border-disabled-checked":b,"--n-box-shadow-focus":h,"--n-color":r,"--n-color-checked":i,"--n-color-table":o,"--n-color-table-modal":s,"--n-color-table-popover":c,"--n-color-disabled":a,"--n-color-disabled-checked":y,"--n-text-color":g,"--n-text-color-disabled":_,"--n-check-mark-color":l,"--n-check-mark-color-disabled":u,"--n-check-mark-color-disabled-checked":v,"--n-font-size":D,"--n-label-padding":S}}),F=o?p(`checkbox`,f(()=>C.value[0]),N,e):void 0;return Object.assign(b,j,{rtlEnabled:M,selfRef:n,mergedClsPrefix:i,mergedDisabled:S,renderedChecked:y,mergedTheme:w,labelId:P(),handleClick:E,handleKeyUp:O,handleKeyDown:k,cssVars:o?void 0:N,themeClass:F?.themeClass,onRender:F?.onRender})},render(){let{$slots:e,renderedChecked:t,mergedDisabled:n,indeterminate:r,privateInsideTable:a,cssVars:o,labelId:l,label:u,mergedClsPrefix:f,focusable:p,handleKeyUp:m,handleKeyDown:g,handleClick:_}=this;this.onRender?.();let v=h(e.default,e=>u||e?(c(),d(`span`,{key:1,class:C(`${f}-checkbox__label`),id:l},[w(()=>u||e)],10,G)):null);return(()=>{let e=y(`70be6e74cd27cb50`);return c(),d(`div`,{ref:`selfRef`,class:C([`${f}-checkbox`,this.themeClass,this.rtlEnabled&&`${f}-checkbox--rtl`,t&&`${f}-checkbox--checked`,n&&`${f}-checkbox--disabled`,r&&`${f}-checkbox--indeterminate`,a&&`${f}-checkbox--inside-table`,v&&`${f}-checkbox--show-label`]),tabindex:n||!p?void 0:0,role:`checkbox`,"aria-checked":r?`mixed`:t,"aria-labelledby":l,style:S(o),onKeyup:m,onKeydown:g,onClick:_,onMousedown:e[0]||=()=>{s(`selectstart`,window,e=>{e.preventDefault()},{once:!0})}},[T(`div`,{class:C(`${f}-checkbox-box-wrapper`)},[e[1]||=w(`\xA0`,-1),T(`div`,{class:C(`${f}-checkbox-box`)},[i(I,null,{default:()=>this.indeterminate?(c(),d(`div`,{key:`indeterminate`,class:C(`${f}-checkbox-icon`)},[w(()=>U())],2)):(c(),d(`div`,{key:`check`,class:C(`${f}-checkbox-icon`)},[w(()=>H())],2))},1024),T(`div`,{class:C(`${f}-checkbox-box__border`)},null,2)],2)],2),w(()=>v)],46,K)})()}}),Y=n(`n-checkbox-group`),X=o({name:`CheckboxGroup`,props:{min:Number,max:Number,size:String,options:Array,labelField:{type:String,default:`label`},valueField:{type:String,default:`value`},value:Array,defaultValue:{type:Array,default:null},disabled:{type:Boolean,default:void 0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],onChange:[Function,Array]},setup(e){let{mergedClsPrefixRef:t}=v(e),n=r(e),{mergedSizeRef:i,mergedDisabledRef:o}=n,s=A(e.defaultValue),c=f(()=>e.value),l=a(c,s),u=f(()=>l.value?.length||0),d=f(()=>Array.isArray(l.value)?new Set(l.value):new Set);function p(t,r){let{nTriggerFormInput:i,nTriggerFormChange:a}=n,{onChange:o,"onUpdate:value":c,onUpdateValue:u}=e;if(Array.isArray(l.value)){let e=Array.from(l.value),n=e.findIndex(e=>e===r);t?~n||(e.push(r),u&&m(u,e,{actionType:`check`,value:r}),c&&m(c,e,{actionType:`check`,value:r}),i(),a(),s.value=e,o&&m(o,e)):~n&&(e.splice(n,1),u&&m(u,e,{actionType:`uncheck`,value:r}),c&&m(c,e,{actionType:`uncheck`,value:r}),o&&m(o,e),s.value=e,i(),a())}else t?(u&&m(u,[r],{actionType:`check`,value:r}),c&&m(c,[r],{actionType:`check`,value:r}),o&&m(o,[r]),s.value=[r],i(),a()):(u&&m(u,[],{actionType:`uncheck`,value:r}),c&&m(c,[],{actionType:`uncheck`,value:r}),o&&m(o,[]),s.value=[],i(),a())}return g(Y,{checkedCountRef:u,maxRef:D(e,`max`),minRef:D(e,`min`),valueSetRef:d,disabledRef:o,mergedSizeRef:i,toggleCheckbox:p}),{mergedClsPrefix:t}},render(){let{options:t,labelField:n,valueField:r}=this.$props;return c(),d(`div`,{class:C(`${this.mergedClsPrefix}-checkbox-group`),role:`group`},[t?(c(),d(L,{key:0},[w(()=>t.map(t=>{let i=t[r];return c(),e(J,{key:i,value:i,disabled:t.disabled,label:t[n]},null,8,[`value`,`disabled`,`label`])}))],64)):(c(),d(L,{key:1},[w(()=>this.$slots.default?.())],64))],2)}});export{J as n,V as r,X as t};