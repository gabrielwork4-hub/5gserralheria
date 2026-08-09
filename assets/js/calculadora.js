/* ==========================================================================
   5G SERRALHERIA - CALCULADORA DE ESCADA
   Vanilla JS. Mesma matematica da tabela de referencia estatica da pagina.
   ========================================================================== */

(function () {
  'use strict';

  // Referencias de dimensionamento para uso residencial.
  const ESPELHO_ALVO = 17.5;   // cm, centro da faixa confortavel
  const ESPELHO_MIN = 16.0;
  const ESPELHO_MAX = 19.0;
  const PISO_MIN = 27.0;       // minimo para o pe apoiar inteiro
  const BLONDEL = 64.0;        // 2e + p, centro da faixa 63-65

  /**
   * Dimensiona a escada para uma altura entre pisos acabados.
   * @param {number} alturaCm altura total em cm
   * @param {number} degraus  numero de degraus (opcional; calculado se omitido)
   */
  function dimensionar(alturaCm, degraus) {
    const n = degraus || Math.max(2, Math.round(alturaCm / ESPELHO_ALVO));
    const espelho = alturaCm / n;
    const pisoBlondel = BLONDEL - 2 * espelho;
    const piso = Math.max(pisoBlondel, PISO_MIN);
    const pisoTravado = pisoBlondel < PISO_MIN;
    return {
      degraus: n,
      espelho: espelho,
      piso: piso,
      pisoTravado: pisoTravado,
      comprimento: (n - 1) * piso,   // o ultimo degrau e o proprio andar de cima
      blondel: 2 * espelho + piso,
      espelhoOk: espelho >= ESPELHO_MIN && espelho <= ESPELHO_MAX
    };
  }

  const cm = (v) => v.toFixed(1).replace('.', ',') + ' cm';
  const m = (v) => (v / 100).toFixed(2).replace('.', ',') + ' m';

  function render(alturaCm, comprimentoCm) {
    const base = dimensionar(alturaCm);
    const alternativas = [
      dimensionar(alturaCm, base.degraus - 1),
      dimensionar(alturaCm, base.degraus + 1)
    ].filter((a) => a.degraus >= 2 && a.espelhoOk);

    const cabe = comprimentoCm ? comprimentoCm >= base.comprimento : null;

    let avisos = '';
    if (!base.espelhoOk) {
      avisos += '<li class="calc-aviso-alerta">O espelho de ' + cm(base.espelho) +
        ' está fora da faixa confortável (17 cm a 18,5 cm). Confira se a altura informada está correta.</li>';
    }
    if (base.pisoTravado) {
      avisos += '<li class="calc-aviso-alerta">Pela regra de Blondel o piso ficaria abaixo de 27 cm, então travamos no mínimo. ' +
        'Com esse espelho, a escada fica no limite do confortável.</li>';
    }
    if (cabe === false) {
      avisos += '<li class="calc-aviso-alerta">Não cabe no comprimento informado: faltam ' +
        m(base.comprimento - comprimentoCm) + '. Considere escada em L, em U ou caracol — ' +
        'aumentar o espelho para encurtar a escada deixa a subida cansativa.</li>';
    }
    if (cabe === true) {
      avisos += '<li class="calc-aviso-ok">Cabe no comprimento informado, com folga de ' +
        m(comprimentoCm - base.comprimento) + '.</li>';
    }

    let alt = '';
    if (alternativas.length) {
      alt = '<h4>Alternativas dentro da faixa aceitável</h4><div class="tabela-scroll">' +
        '<table class="tabela-dados"><thead><tr>' +
        '<th scope="col">Degraus</th><th scope="col">Espelho</th><th scope="col">Piso</th>' +
        '<th scope="col">Comprimento</th></tr></thead><tbody>' +
        alternativas.map((a) =>
          '<tr><td>' + a.degraus + '</td><td>' + cm(a.espelho) + '</td><td>' + cm(a.piso) +
          '</td><td>' + m(a.comprimento) + '</td></tr>').join('') +
        '</tbody></table></div>';
    }

    return '' +
      '<h3 class="calc-resultado-titulo">Para ' + m(alturaCm) + ' entre pisos acabados</h3>' +
      '<div class="calc-cards">' +
        '<div class="calc-card"><span class="calc-card-val">' + base.degraus + '</span><span class="calc-card-lbl">degraus</span></div>' +
        '<div class="calc-card"><span class="calc-card-val">' + cm(base.espelho) + '</span><span class="calc-card-lbl">espelho</span></div>' +
        '<div class="calc-card"><span class="calc-card-val">' + cm(base.piso) + '</span><span class="calc-card-lbl">piso</span></div>' +
        '<div class="calc-card"><span class="calc-card-val">' + m(base.comprimento) + '</span><span class="calc-card-lbl">comprimento ocupado</span></div>' +
      '</div>' +
      '<p class="calc-blondel">Verificação de Blondel: 2 × ' + cm(base.espelho) + ' + ' + cm(base.piso) +
        ' = <strong>' + cm(base.blondel) + '</strong> — dentro da faixa de 63 cm a 65 cm.</p>' +
      (avisos ? '<ul class="calc-avisos">' + avisos + '</ul>' : '') +
      alt +
      '<p class="calc-rodape">Escada reta, sem patamar. O resultado dimensiona o degrau: apoio estrutural, ' +
        'altura livre de passagem e acesso para instalação só a visita técnica confirma.</p>' +
      '<a href="https://wa.me/5511966408235?text=' +
        encodeURIComponent('Olá! Usei a calculadora de escada. Altura entre pisos: ' +
          (alturaCm / 100).toFixed(2) + ' m, resultado ' + base.degraus + ' degraus. Gostaria de um orçamento.') +
        '" class="btn btn-whatsapp calc-cta" target="_blank" rel="noopener">Enviar este resultado no WhatsApp</a>';
  }

  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('calcForm');
    if (!form) return;

    const saida = document.getElementById('calcResultado');
    const erro = document.getElementById('calcErro');

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      const altura = parseFloat(document.getElementById('altura').value);
      const compRaw = document.getElementById('comprimento').value;
      const comprimento = compRaw ? parseFloat(compRaw) : null;

      erro.hidden = true;
      erro.textContent = '';

      if (!altura || isNaN(altura)) {
        erro.textContent = 'Informe a altura entre os pisos acabados, em centímetros.';
        erro.hidden = false;
        saida.hidden = true;
        return;
      }
      if (altura < 100 || altura > 600) {
        erro.textContent = 'A altura deve ficar entre 100 cm e 600 cm. Confira se o valor está em centímetros — 2,80 m se escreve 280.';
        erro.hidden = false;
        saida.hidden = true;
        return;
      }
      if (comprimento !== null && (isNaN(comprimento) || comprimento < 50)) {
        erro.textContent = 'O comprimento disponível deve ser um valor em centímetros a partir de 50.';
        erro.hidden = false;
        saida.hidden = true;
        return;
      }

      saida.innerHTML = render(altura, comprimento);
      saida.hidden = false;

      if (typeof window.gtag === 'function') {
        window.gtag('event', 'usou_calculadora', {
          ferramenta: 'calculadora-escada',
          altura_cm: altura,
          pagina: window.location.pathname
        });
      }
    });
  });
})();
