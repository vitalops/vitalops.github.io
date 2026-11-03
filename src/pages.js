/* company site: nav dropdowns, the mobile menu lock and the lifecycle tabs (src/pages.js) */
(function(){
  var drops=[].slice.call(document.querySelectorAll('.nav-drop'));
  function closeAll(except){drops.forEach(function(d){if(d!==except){d.classList.remove('open');d.querySelector('.nav-drop-btn').setAttribute('aria-expanded','false');}});}
  drops.forEach(function(d){
    var b=d.querySelector('.nav-drop-btn');
    b.addEventListener('click',function(e){e.stopPropagation();var o=!d.classList.contains('open');closeAll(d);d.classList.toggle('open',o);b.setAttribute('aria-expanded',o?'true':'false');});
  });
  document.addEventListener('click',function(e){if(!e.target.closest('.nav-drop'))closeAll();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')closeAll();});
  var t=document.getElementById('navToggle'),l=document.getElementById('navLinks');
  if(t&&l){
    new MutationObserver(function(){document.body.classList.toggle('nav-open',l.classList.contains('open'));}).observe(l,{attributes:true,attributeFilter:['class']});
    addEventListener('resize',function(){if(innerWidth>1040&&l.classList.contains('open')){l.classList.remove('open');t.setAttribute('aria-expanded','false');}});
  }
  var rail=document.querySelector('.lc-rail');
  if(rail){
    var cards=[].slice.call(rail.querySelectorAll('.lc-card'));
    function pick(c,focus){cards.forEach(function(x){var on=x===c;x.classList.toggle('on',on);x.setAttribute('aria-selected',on?'true':'false');x.tabIndex=on?0:-1;var p=document.getElementById(x.getAttribute('aria-controls'));if(p)p.hidden=!on;});if(focus)c.focus();}
    cards.forEach(function(c,i){c.tabIndex=i?-1:0;c.addEventListener('click',function(){pick(c);});
      c.addEventListener('keydown',function(e){var k=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;if(k){e.preventDefault();pick(cards[(i+k+cards.length)%cards.length],true);}});});
  }
})();
