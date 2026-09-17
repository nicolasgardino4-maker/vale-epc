document.addEventListener('DOMContentLoaded', () => {
  const page = window.location.pathname.includes('/nuevo') ? 'nuevo' : 'panel';

  if (page === 'nuevo') {
    initNuevoVale();
    return;
  }

  initPanel();
});

function showMessage(text, isError = false) {
  const el = document.getElementById('mensaje');
  if (!el) return;
  el.textContent = text;
  el.classList.remove('oculto');
  el.style.background = isError ? '#fee2e2' : '#dbeafe';
  el.style.borderColor = isError ? '#fca5a5' : '#93c5fd';
  el.style.color = isError ? '#991b1b' : '#1e3a8a';
}

function initPanel() {
  const template = document.getElementById('vale-template');
  const list = document.getElementById('lista-vales');
  const modal = document.getElementById('modal');
  const detalle = document.getElementById('detalle-vale');

  let estadoActual = '';

  const fetchVales = async () => {
    try {
      const res = await fetch(`/api/vales?estado=${estadoActual}`, { credentials: 'same-origin' });
      if (!res.ok) {
        throw new Error('No se pudieron cargar los vales');
      }

      const vales = await res.json();
      list.innerHTML = '';

      if (!vales.length) {
        list.innerHTML = '<p>No hay vales para mostrar.</p>';
        return;
      }

      vales.forEach((vale) => {
        const node = template.content.firstElementChild.cloneNode(true);
        node.querySelector('.estado').textContent = vale.estado || 'pendiente';
        node.querySelector('.estado').classList.add(vale.estado || 'pendiente');
        node.querySelector('.codigo').textContent = `Vale #${vale.id}`;
        node.querySelector('.nombre').textContent = vale.apellido_nombre || 'Sin nombre';
        node.querySelector('.obra').textContent = vale.obra || 'Sin obra';
        node.querySelector('.fecha').textContent = vale.fecha || 'Sin fecha';

        const ul = node.querySelector('.items');
        (vale.items || []).forEach((item) => {
          const li = document.createElement('li');
          li.textContent = `${item.descripcion || 'Sin descripción'} (${item.cantidad || '0'})`;
          ul.appendChild(li);
        });

        node.querySelector('.ver-vale').addEventListener('click', () => openDetalle(vale));
        node.querySelector('.autorizar').addEventListener('click', () => autorizarVale(vale.id));
        node.querySelector('.ingresado').addEventListener('click', () => marcarIngresado(vale.id));

        list.appendChild(node);
      });
    } catch (error) {
      showMessage(error.message, true);
    }
  };

  const openDetalle = async (vale) => {
    try {
      const res = await fetch(`/api/vales/${vale.id}`, { credentials: 'same-origin' });
      const data = await res.json();
      detalle.innerHTML = `
        <div class="detalle-card">
          <h2>Vale ${data.id}</h2>
          <div class="detalle-grid">
            <div><strong>Solicitante:</strong> ${data.apellido_nombre || ''}</div>
            <div><strong>DNI / Legajo:</strong> ${data.dni_legajo || ''}</div>
            <div><strong>Obra:</strong> ${data.obra || ''}</div>
            <div><strong>Fecha:</strong> ${data.fecha || ''}</div>
            <div><strong>Estado:</strong> ${data.estado || 'pendiente'}</div>
            <div><strong>Creado:</strong> ${data.creado_en || ''}</div>
          </div>
          <p><strong>Observaciones:</strong> ${data.observaciones || ''}</p>
          <h3>Ítems</h3>
          <ul>
            ${(data.items || []).map(item => `<li>${item.descripcion || 'Sin descripción'} — cantidad: ${item.cantidad || '0'} — entregado: ${item.entregado || ''}</li>`).join('')}
          </ul>
        </div>
      `;
      modal.classList.remove('oculto');
    } catch (error) {
      showMessage(error.message, true);
    }
  };

  const autorizarVale = async (id) => {
    const firma = window.prompt('Ingresá la firma del autorizante');
    if (!firma) return;

    try {
      const res = await fetch(`/api/vales/${id}/autorizar`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ firma_autorizante: firma })
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || 'No se pudo autorizar');
      showMessage('Vale autorizado correctamente');
      fetchVales();
    } catch (error) {
      showMessage(error.message, true);
    }
  };

  const marcarIngresado = async (id) => {
    try {
      const res = await fetch(`/api/vales/${id}/ingresado`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingresado: true })
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || 'No se pudo marcar como ingresado');
      showMessage('Vale marcado como ingresado');
      fetchVales();
    } catch (error) {
      showMessage(error.message, true);
    }
  };

  document.querySelectorAll('.filter').forEach((btn) => {
    btn.addEventListener('click', () => {
      estadoActual = btn.dataset.estado || '';
      document.querySelectorAll('.filter').forEach((b) => b.classList.toggle('active', b === btn));
      fetchVales();
    });
  });

  document.querySelector('.close-modal')?.addEventListener('click', () => modal.classList.add('oculto'));
  modal.addEventListener('click', (event) => {
    if (event.target === modal) {
      modal.classList.add('oculto');
    }
  });

  fetchVales();
}

function initNuevoVale() {
  const container = document.getElementById('items-container');
  const template = document.getElementById('item-template');

  const addItem = () => {
    const row = template.content.firstElementChild.cloneNode(true);
    container.appendChild(row);
    row.querySelector('.remove-item').addEventListener('click', () => row.remove());
  };

  document.getElementById('agregar-item').addEventListener('click', addItem);

  addItem();

  document.getElementById('form-vale').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);

    const items = [...container.querySelectorAll('.item-row')].map((row) => {
      const inputs = row.querySelectorAll('input');
      return {
        codigo: inputs[0].value,
        descripcion: inputs[1].value,
        cantidad: inputs[2].value,
        entregado: inputs[3].value
      };
    }).filter((item) => item.descripcion.trim() || item.codigo.trim() || item.cantidad.trim());

    const payload = {
      n_vale: formData.get('n_vale')?.toString() || '',
      fecha: formData.get('fecha')?.toString() || '',
      obra: formData.get('obra')?.toString() || '',
      apellido_nombre: formData.get('apellido_nombre')?.toString() || '',
      dni_legajo: formData.get('dni_legajo')?.toString() || '',
      observaciones: formData.get('observaciones')?.toString() || '',
      firma_solicitante: formData.get('firma_solicitante')?.toString() || '',
      items
    };

    try {
      const res = await fetch('/api/vales', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.error || 'No se pudo guardar el vale');
      alert('Vale cargado correctamente');
      form.reset();
      container.innerHTML = '';
      addItem();
    } catch (error) {
      alert(error.message);
    }
  });
}
