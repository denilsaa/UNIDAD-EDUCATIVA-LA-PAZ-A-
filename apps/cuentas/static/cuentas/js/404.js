(function(){
  const secsEl = document.getElementById("secs");
  const btn = document.getElementById("btn-volver");
  const tplPrev = btn ? btn.getAttribute("href") : "/";
  let secs = parseInt(secsEl ? secsEl.textContent : "5", 10) || 5;

  function goBack(){
    if (tplPrev && tplPrev !== window.location.href) {
      window.location.replace(tplPrev);               // última OK guardada
    } else if (window.history.length > 1) {
      window.history.back();
    } else {
      // Fallback al dashboard de cuentas (ajuste el name si es otro)
      window.location.replace("{% url 'cuentas:director_dashboard' %}");
    }
  }

  const timer = setInterval(function(){
    secs--;
    if (secsEl) secsEl.textContent = String(secs);
    if (secs <= 0){
      clearInterval(timer);
      goBack();
    }
  }, 1000);

  btn && btn.addEventListener("click", function(e){
    e.preventDefault();
    goBack();
  });
})();