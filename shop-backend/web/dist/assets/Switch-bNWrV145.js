import{An as e,Bn as t,C as n,E as r,G as i,In as a,Jn as o,Mn as s,On as c,Q as l,R as u,U as d,V as f,Z as p,bt as m,dn as h,et as g,fn as _,fr as v,ft as y,ht as b,kn as x,ln as S,lr as C,lt as w,on as T,or as E,ot as D,rt as O,sn as k,un as A,w as j,x as M}from"./_plugin-vue_export-helper-Z-C6jLwj.js";var N={buttonHeightSmall:`14px`,buttonHeightMedium:`18px`,buttonHeightLarge:`22px`,buttonWidthSmall:`14px`,buttonWidthMedium:`18px`,buttonWidthLarge:`22px`,buttonWidthPressedSmall:`20px`,buttonWidthPressedMedium:`24px`,buttonWidthPressedLarge:`28px`,railHeightSmall:`18px`,railHeightMedium:`22px`,railHeightLarge:`26px`,railWidthSmall:`32px`,railWidthMedium:`40px`,railWidthLarge:`48px`};function P(e){let{primaryColor:t,opacityDisabled:n,borderRadius:r,textColor3:i}=e;return{...N,iconColor:i,textColor:`white`,loadingColor:t,opacityDisabled:n,railColor:`rgba(0, 0, 0, .14)`,railColorActive:t,buttonBoxShadow:`0 1px 4px 0 rgba(0, 0, 0, 0.3), inset 0 0 1px 0 rgba(0, 0, 0, 0.05)`,buttonColor:`#FFF`,railBorderRadiusSmall:r,railBorderRadiusMedium:r,railBorderRadiusLarge:r,buttonBorderRadiusSmall:r,buttonBorderRadiusMedium:r,buttonBorderRadiusLarge:r,boxShadowFocus:`0 0 0 2px ${O(t,{alpha:.2})}`}}var F={name:`Switch`,common:g,self:P},I=k(`switch`,`
 height: var(--n-height);
 min-width: var(--n-width);
 vertical-align: middle;
 user-select: none;
 -webkit-user-select: none;
 display: inline-flex;
 outline: none;
 justify-content: center;
 align-items: center;
`,[S(`children-placeholder`,`
 height: var(--n-rail-height);
 display: flex;
 flex-direction: column;
 overflow: hidden;
 pointer-events: none;
 visibility: hidden;
 `),S(`rail-placeholder`,`
 display: flex;
 flex-wrap: none;
 `),S(`button-placeholder`,`
 width: calc(1.75 * var(--n-rail-height));
 height: var(--n-rail-height);
 `),k(`base-loading`,`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 font-size: calc(var(--n-button-width) - 4px);
 color: var(--n-loading-color);
 transition: color .3s var(--n-bezier);
 `,[n({left:`50%`,top:`50%`,originalTransform:`translateX(-50%) translateY(-50%)`})]),S(`checked, unchecked`,`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 box-sizing: border-box;
 position: absolute;
 white-space: nowrap;
 top: 0;
 bottom: 0;
 display: flex;
 align-items: center;
 line-height: 1;
 `),S(`checked`,`
 right: 0;
 padding-right: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),S(`unchecked`,`
 left: 0;
 justify-content: flex-end;
 padding-left: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),T(`&:focus`,[S(`rail`,`
 box-shadow: var(--n-box-shadow-focus);
 `)]),A(`round`,[S(`rail`,`border-radius: calc(var(--n-rail-height) / 2);`,[S(`button`,`border-radius: calc(var(--n-button-height) / 2);`)])]),h(`disabled`,[h(`icon`,[A(`rubber-band`,[A(`pressed`,[S(`rail`,[S(`button`,`max-width: var(--n-button-width-pressed);`)])]),S(`rail`,[T(`&:active`,[S(`button`,`max-width: var(--n-button-width-pressed);`)])]),A(`active`,[A(`pressed`,[S(`rail`,[S(`button`,`left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));`)])]),S(`rail`,[T(`&:active`,[S(`button`,`left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));`)])])])])])]),A(`active`,[S(`rail`,[S(`button`,`left: calc(100% - var(--n-button-width) - var(--n-offset))`)])]),S(`rail`,`
 overflow: hidden;
 height: var(--n-rail-height);
 min-width: var(--n-rail-width);
 border-radius: var(--n-rail-border-radius);
 cursor: pointer;
 position: relative;
 transition:
 opacity .3s var(--n-bezier),
 background .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 background-color: var(--n-rail-color);
 `,[S(`button-icon`,`
 color: var(--n-icon-color);
 transition: color .3s var(--n-bezier);
 font-size: calc(var(--n-button-height) - 4px);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 display: flex;
 justify-content: center;
 align-items: center;
 line-height: 1;
 `,[n()]),S(`button`,`
 align-items: center; 
 top: var(--n-offset);
 left: var(--n-offset);
 height: var(--n-button-height);
 width: var(--n-button-width-pressed);
 max-width: var(--n-button-width);
 border-radius: var(--n-button-border-radius);
 background-color: var(--n-button-color);
 box-shadow: var(--n-button-box-shadow);
 box-sizing: border-box;
 cursor: inherit;
 content: "";
 position: absolute;
 transition:
 background-color .3s var(--n-bezier),
 left .3s var(--n-bezier),
 opacity .3s var(--n-bezier),
 max-width .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 `)]),A(`active`,[S(`rail`,`background-color: var(--n-rail-color-active);`)]),A(`loading`,[S(`rail`,`
 cursor: wait;
 `)]),A(`disabled`,[S(`rail`,`
 cursor: not-allowed;
 opacity: .5;
 `)])]),L=[`aria-checked`,`tabindex`,`onClick`,`onFocus`,`onBlur`,`onKeyup`,`onKeydown`],R={...p.props,size:String,value:{type:[String,Number,Boolean],default:void 0},loading:Boolean,defaultValue:{type:[String,Number,Boolean],default:!1},disabled:{type:Boolean,default:void 0},round:{type:Boolean,default:!0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],checkedValue:{type:[String,Number,Boolean],default:!0},uncheckedValue:{type:[String,Number,Boolean],default:!1},railStyle:Function,rubberBand:{type:Boolean,default:!0},spinProps:Object,onChange:[Function,Array]},z,B=a({name:`Switch`,props:R,slots:Object,setup(e){z===void 0&&(z=typeof CSS<`u`?CSS.supports!==void 0&&CSS.supports(`width`,`max(1px)`):!0);let{mergedClsPrefixRef:t,inlineThemeDisabled:n,mergedComponentPropsRef:a}=m(e),o=p(`Switch`,`-switch`,I,F,e,t),s=r(e,{mergedSize(t){return e.size===void 0?t?t.mergedSize.value:a?.value?.Switch?.size||`medium`:e.size}}),{mergedSizeRef:u,mergedDisabledRef:f}=s,h=E(e.defaultValue),g=C(e,`value`),v=i(g,h),y=c(()=>v.value===e.checkedValue),b=E(!1),x=E(!1),S=c(()=>{let{railStyle:t}=e;if(t)return t({focused:x.value,checked:y.value})});function T(t){let{"onUpdate:value":n,onChange:r,onUpdateValue:i}=e,{nTriggerFormInput:a,nTriggerFormChange:o}=s;n&&d(n,t),i&&d(i,t),r&&d(r,t),h.value=t,a(),o()}function O(){let{nTriggerFormFocus:e}=s;e()}function k(){let{nTriggerFormBlur:e}=s;e()}function A(){e.loading||f.value||(v.value===e.checkedValue?T(e.uncheckedValue):T(e.checkedValue))}function j(){x.value=!0,O()}function M(){x.value=!1,k(),b.value=!1}function N(t){e.loading||f.value||t.key===` `&&(v.value===e.checkedValue?T(e.uncheckedValue):T(e.checkedValue),b.value=!1)}function P(t){e.loading||f.value||t.key===` `&&(t.preventDefault(),b.value=!0)}let L=c(()=>{let{value:e}=u,{self:{opacityDisabled:t,railColor:n,railColorActive:r,buttonBoxShadow:i,buttonColor:a,boxShadowFocus:s,loadingColor:c,textColor:l,iconColor:d,[_(`buttonHeight`,e)]:f,[_(`buttonWidth`,e)]:p,[_(`buttonWidthPressed`,e)]:m,[_(`railHeight`,e)]:h,[_(`railWidth`,e)]:g,[_(`railBorderRadius`,e)]:v,[_(`buttonBorderRadius`,e)]:y},common:{cubicBezierEaseInOut:b}}=o.value,x,S,C;return z?(x=`calc((${h} - ${f}) / 2)`,S=`max(${h}, ${f})`,C=`max(${g}, calc(${g} + ${f} - ${h}))`):(x=w((D(h)-D(f))/2),S=w(Math.max(D(h),D(f))),C=D(h)>D(f)?g:w(D(g)+D(f)-D(h))),{"--n-bezier":b,"--n-button-border-radius":y,"--n-button-box-shadow":i,"--n-button-color":a,"--n-button-width":p,"--n-button-width-pressed":m,"--n-button-height":f,"--n-height":S,"--n-offset":x,"--n-opacity-disabled":t,"--n-rail-border-radius":v,"--n-rail-color":n,"--n-rail-color-active":r,"--n-rail-height":h,"--n-rail-width":g,"--n-width":C,"--n-box-shadow-focus":s,"--n-loading-color":c,"--n-text-color":l,"--n-icon-color":d}}),R=n?l(`switch`,c(()=>u.value[0]),L,e):void 0;return{handleClick:A,handleBlur:M,handleFocus:j,handleKeyup:N,handleKeydown:P,mergedRailStyle:S,pressed:b,mergedClsPrefix:t,mergedValue:v,checked:y,mergedDisabled:f,cssVars:n?void 0:L,themeClass:R?.themeClass,onRender:R?.onRender}},render(){let{mergedClsPrefix:n,mergedDisabled:r,checked:i,mergedRailStyle:a,onRender:c,$slots:l}=this;c?.();let{checked:d,unchecked:p,icon:m,"checked-icon":h,"unchecked-icon":g}=l,_=!(u(m)&&u(h)&&u(g));return o(),s(`div`,{role:`switch`,"aria-checked":i,class:y([`${n}-switch`,this.themeClass,_&&`${n}-switch--icon`,i&&`${n}-switch--active`,r&&`${n}-switch--disabled`,this.round&&`${n}-switch--round`,this.loading&&`${n}-switch--loading`,this.pressed&&`${n}-switch--pressed`,this.rubberBand&&`${n}-switch--rubber-band`]),tabindex:this.mergedDisabled?void 0:0,style:v(this.cssVars),onClick:this.handleClick,onFocus:this.handleFocus,onBlur:this.handleBlur,onKeyup:this.handleKeyup,onKeydown:this.handleKeydown},[x(`div`,{class:y(`${n}-switch__rail`),"aria-hidden":`true`,style:v(a)},[b(()=>f(d,e=>f(p,t=>e||t?(o(),s(`div`,{key:4,"aria-hidden":!0,class:y(`${n}-switch__children-placeholder`)},[x(`div`,{class:y(`${n}-switch__rail-placeholder`)},[x(`div`,{class:y(`${n}-switch__button-placeholder`)},null,2),b(()=>e)],2),x(`div`,{class:y(`${n}-switch__rail-placeholder`)},[x(`div`,{class:y(`${n}-switch__button-placeholder`)},null,2),b(()=>t)],2)],2)):null))),x(`div`,{class:y(`${n}-switch__button`)},[b(()=>f(m,r=>f(h,i=>f(g,a=>(o(),e(j,null,{default:()=>this.loading?(o(),e(M,t({key:`loading`,clsPrefix:n,strokeWidth:20},this.spinProps),null,16,[`clsPrefix`])):this.checked&&(i||r)?(o(),s(`div`,{class:y(`${n}-switch__button-icon`),key:i?`checked-icon`:`icon`},[b(()=>i||r)],2)):!this.checked&&(a||r)?(o(),s(`div`,{class:y(`${n}-switch__button-icon`),key:a?`unchecked-icon`:`icon`},[b(()=>a||r)],2)):null},1024)))))),b(()=>f(d,e=>e&&(o(),s(`div`,{key:`checked`,class:y(`${n}-switch__checked`)},[b(()=>e)],2)))),b(()=>f(p,e=>e&&(o(),s(`div`,{key:`unchecked`,class:y(`${n}-switch__unchecked`)},[b(()=>e)],2))))],2)],6)],46,L)}});export{B as t};