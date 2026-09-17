# Sistema de Vales — EPC

App para reemplazar la planilla en papel "PLANILLA CARGO DIARIO" / Vale de
materiales. Se carga desde el celular, avisa en la PC con sonido y cartel,
y se autoriza firmando con el mouse.

Esta versión vive en la nube: no depende de que ninguna PC esté prendida
ni de instalar nada. Tanto desde el celular como desde la PC, se entra con
el navegador a una dirección web fija.

Para armarlo se necesitan 3 cuentas gratuitas (una sola vez cada una):

| Servicio | Para qué |
|---|---|
| **Neon** | Guarda los datos (base de datos Postgres gratis) |
| **GitHub** | Guarda el código del sistema |
| **Render** | Corre el sistema todo el tiempo y le da la dirección web |

## 1) Creá la base de datos en Neon

1. Entrá a https://neon.tech y creá una cuenta gratis (podés usar GitHub o Google).
2. Creá un proyecto nuevo (te va a proponer un nombre, dejalo como está o
   ponele "vales-epc").
3. En el panel del proyecto buscá **"Connection string"** — es un texto
   largo que empieza con `postgresql://...`. Copialo, lo vas a necesitar
   en el paso 3.

## 2) Subí el código a GitHub

1. Entrá a https://github.com y creá una cuenta gratis (si no tenés).
2. Arriba a la derecha, `+` → **New repository**. Ponele de nombre
   `vales-epc`, dejalo en "Public" o "Private" (como prefieras), y creá el
   repositorio (no hace falta tildar nada más).
3. Dentro del repositorio vacío, buscá el link que dice
   **"uploading an existing file"**.
4. Arrastrá ahí TODOS los archivos y carpetas de esta carpeta
   (`app.py`, `requirements.txt`, `Procfile`, `render.yaml`, `templates/`,
   `static/`) y confirmá con **"Commit changes"**.

No hace falta usar git ni la consola para esto, se hace todo arrastrando
los archivos desde la página de GitHub.

## 3) Desplegalo en Render

1. Entrá a https://render.com y creá una cuenta gratis (podés entrar
directo con tu cuenta de GitHub, así quedan conectadas).
2. **New +** → **Web Service**.
3. Elegí el repositorio `vales-epc` que subiste en el paso 2.
4. Render va a detectar solo el `render.yaml` y te va a pedir completar
   las variables de entorno:
   - `DATABASE_URL` → pegá el connection string de Neon (paso 1.3)
   - `USUARIO` → el usuario que quieras para entrar al sistema
   - `CONTRASENA` → la contraseña que quieras
5. Confirmá la creación. Render va a instalar todo y arrancar el sistema
   solo — tarda unos minutos la primera vez.
6. Cuando termine, arriba vas a ver la dirección del sistema, algo como:
   `https://vales-epc.onrender.com`

Esa dirección ya es definitiva y no cambia.

## 4) Usarlo

- **Desde el celular** (datos o WiFi, sin ninguna app extra), para cargar
  un vale:
  `https://vales-epc.onrender.com/nuevo`
  Va a pedir el usuario y contraseña del paso 3.4 la primera vez.

- **En la PC**, para ver los vales, escuchar el aviso y autorizar firmando
  con el mouse:
  `https://vales-epc.onrender.com/panel`

Dejá esa pestaña del panel abierta en la PC (en cualquier navegador):
cuando llega un vale nuevo desde el celular, suena un aviso y aparece un
cartel arriba a la derecha con el nombre del solicitante y la obra. Desde
ahí entrás directo a firmarlo.

### Tip

Guardá el link terminado en `/nuevo` como acceso directo en la pantalla de
inicio del celular (Chrome: menú ⋮ > Agregar a pantalla de inicio).

## 5) Cómo funciona el flujo

1. El solicitante completa el vale desde el celular (datos, ítems, firma
   con el dedo) y lo envía.
2. En la PC, mientras el panel esté abierto, suena un aviso y aparece el
   cartel.
3. Hacés clic en "Ver", revisás los datos y firmás con el mouse como
   autorizante.
4. Al autorizar, el vale pasa a "autorizado". Desde ahí podés marcarlo
   como "ingresado a stock" una vez que cargaste el movimiento
   correspondiente en Mi Depósito (por ahora es solo un tilde de control;
   si más adelante querés que dispare el movimiento automáticamente, se
   puede conectar como un siguiente paso).

## 6) Notas importantes

- **Plan gratuito de Render**: el servicio "se duerme" después de 15
  minutos sin uso, y tarda unos 20-30 segundos en "despertarse" la
  primera vez que alguien entra después de estar dormido (después anda
  normal). Si esto te molesta para el uso diario, se puede pasar al plan
  pago de Render (arranca en unos USD 7/mes) para que esté siempre
  despierto al instante.
- **Plan gratuito de Neon**: la base de datos queda guardada de forma
  permanente (a diferencia del plan gratis de Render, que borra archivos
  locales — por eso usamos Neon para los datos y no un archivo).
- El aviso sonoro en el panel funciona mientras la pestaña esté abierta
  (revisa cada 4 segundos si hay vales nuevos). No es una notificación
  del sistema operativo.
- Las firmas se guardan como imagen (PNG) dentro de la base de datos.
- Si en algún momento cambiás algo del código y volvés a subirlo a
  GitHub, Render lo redespliega solo, sin que tengas que hacer nada en
  Render.

## 7) Probarlo en tu PC antes de subirlo (opcional)

Si en algún momento querés probar cambios antes de subirlos, podés
correrlo local:
```
pip install -r requirements.txt
python app.py
```
Sin `DATABASE_URL` configurada, usa automáticamente un archivo
`vales.db` local para las pruebas, y queda disponible en
`http://localhost:5000/panel`.
