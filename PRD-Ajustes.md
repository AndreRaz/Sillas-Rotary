PRD — Ajustes de Formulario Socioeconómico: Nombre, Estudios, Ingresos, Silla Previa e IMSS/INFONAVIT
1. Objetivo
Actualizar el formulario de estudio socioeconómico y su integración con backend/base de datos para corregir cinco áreas funcionales:
- Separación estructurada del campo de nombre del beneficiario
- Catálogo cerrado para grado máximo de estudios del tutor
- Restricción estricta de ingreso mensual a enteros con formato visual amigable
- Catálogo cerrado para “¿Cómo obtuvo la silla de ruedas?”
- Soporte para opción No aplica en IMSS e INFONAVIT
El cambio debe mantener consistencia entre:
- UI del formulario
- Payload enviado al backend
- Validaciones de servidor
- Persistencia en PostgreSQL
- Compatibilidad razonable con el esquema actual
---
2. Hallazgos Técnicos Confirmados
2.1 Estado actual del formulario y backend
Actualmente el sistema usa:
- beneficiarios.nombre como un solo campo de texto
- tutores.nombre como un solo campo de texto
- tutores.nivel_estudios como texto libre
- estudios_socioeconomicos.como_obtuvo_silla como texto libre
- tutores.tiene_imss y tutores.tiene_infonavit como booleanos enteros (0/1)
- tutores.ingreso_mensual como REAL
2.2 Política actual de normalización
El backend ya tiene una función centralizada normalize_text() que hace:
1. trim
2. compactación de espacios
3. conversión a MAYÚSCULAS
4. eliminación de acentos/diacríticos
Ejemplo:
- entrada: García López
- persistencia actual: GARCIA LOPEZ
2.3 Inconsistencias detectadas
- El frontend ya no es consistente con un modelo estructurado de nombres porque sigue usando nombre único.
- La opción No aplica para IMSS/INFONAVIT NO cabe en el esquema actual de booleanos estrictos.
- ingreso_mensual hoy permite punto decimal en frontend, aunque la necesidad actual exige solo enteros.
- como_obtuvo_silla hoy acepta cualquier texto, aunque el negocio ahora pide catálogo cerrado.
---
3. Decisiones de Diseño
3.1 Decisión recomendada para Nombre del beneficiario
Se implementará captura separada en UI y payload:
- nombres
- apellido_paterno
- apellido_materno
Y en base de datos:
- se agregarán columnas nuevas para persistencia estructurada
- se mantendrá la columna legado beneficiarios.nombre como nombre completo canónico concatenado
3.2 Decisión recomendada para mayúsculas
Se MANTIENE la política actual de persistencia en MAYÚSCULAS para conservar compatibilidad con el backend existente y el PRD previo.
Regla definida:
- El usuario puede capturar letras y acentos en UI
- El backend persiste en MAYÚSCULAS
- El backend elimina acentos al guardar, mientras siga vigente la estrategia actual de normalize_text()
Ejemplo:
- UI: José Ángel
- DB: JOSE ANGEL
3.3 Decisión recomendada para IMSS/INFONAVIT
Se reutilizan las columnas actuales con semántica triestado:
- 1 = Sí
- 0 = No
- NULL = No aplica
Esto minimiza impacto y evita agregar columnas nuevas innecesarias.
3.4 Decisión recomendada para Ingreso mensual
El ingreso mensual será un entero sin decimales.
- En UI se mostrará con separador de miles
- En payload se enviará como número entero
- En backend se validará como entero no negativo
- En DB puede mantenerse temporalmente en la columna actual REAL, pero solo se persistirán enteros
Nota:
Se recomienda migración futura a INTEGER o NUMERIC(9,0), pero NO es obligatoria para esta iteración.
---
4. Alcance
Incluido
- Beneficiario: separación de nombre
- Tutor 1 y Tutor 2: catálogo de estudios
- Tutor 1 y Tutor 2: restricción de ingreso mensual
- Cierre del estudio: catálogo de obtención de silla
- Tutor 1 y Tutor 2: IMSS/INFONAVIT con No aplica
- Ajustes de validación frontend/backend
- Ajustes de payload
- Ajustes de esquema y migración necesarios
Fuera de alcance
- Separar también el nombre de los tutores en nombres/apellidos
- Cambiar la política global de normalización para preservar acentos en DB
- Reestructuración completa de reportes existentes
- Reescritura del flujo de drafts
---
5. Requerimientos Funcionales
RF-01 — Separación del nombre del beneficiario
El campo actual Nombre Completo del beneficiario debe reemplazarse por tres campos:
- Nombre(s)
- Apellido Paterno
- Apellido Materno
Reglas:
- Nombre(s) requerido
- Apellido Paterno requerido
- Apellido Materno requerido
Validación permitida:
- solo letras
- espacios internos
- caracteres acentuados
- sin números
- sin signos especiales
Regex recomendada en frontend y backend:
^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$
Longitudes:
- nombres: 2 a 60
- apellido_paterno: 2 a 40
- apellido_materno: 2 a 40
Normalización al persistir:
- trim
- compactación de espacios
- mayúsculas
- eliminación de acentos según política vigente
Persistencia:
- beneficiarios.nombres
- beneficiarios.apellido_paterno
- beneficiarios.apellido_materno
- beneficiarios.nombre se conserva como concatenación canónica:
  - NOMBRES + " " + APELLIDO_PATERNO + " " + APELLIDO_MATERNO
RF-02 — Grado máximo de estudios del tutor
El campo nivel_estudios del tutor debe dejar de ser texto libre y pasar a <select>.
Catálogo permitido:
- SIN_ESTUDIOS
- PRIMARIA
- SECUNDARIA
- BACHILLERATO_PREPARATORIA
- CARRERA_TECNICA_TSU
- LICENCIATURA_INGENIERIA
- MAESTRIA
- DOCTORADO
Display en UI:
- Sin estudios
- Primaria
- Secundaria
- Bachillerato / Preparatoria
- Carrera técnica / TSU
- Licenciatura / Ingeniería
- Maestría
- Doctorado
Persistencia recomendada:
- Guardar código canónico, no label visual
No se requiere migración de tipo porque la columna actual ya es TEXT.
RF-03 — Ingreso mensual entero con formato visual
El campo ingreso_mensual del tutor debe aceptar SOLO números enteros.
Restricciones:
- bloquear letras
- bloquear símbolos
- bloquear punto .
- bloquear coma manual como entrada semántica
- permitir únicamente dígitos en el valor lógico
Formato visual:
- mostrar separador de miles en frontend
- ejemplo:
  - entrada lógica: 12500
  - display: 12,500
Payload al backend:
- número entero sin comas
- ejemplo: 12500
Longitud máxima recomendada:
- 7 dígitos lógicos
- rango: 0 a 9999999
Validación backend:
- entero
- no negativo
- máximo 9999999
RF-04 — ¿Cómo obtuvo la silla de ruedas?
El campo como_obtuvo_silla debe dejar de ser texto libre y pasar a <select> condicionado por tuvo_silla_previa.
Catálogo permitido:
- COMPRA
- DONACION
Comportamiento:
- Si tuvo_silla_previa = false:
  - campo deshabilitado
  - valor persistido = NULL
- Si tuvo_silla_previa = true:
  - campo habilitado
  - campo obligatorio
  - solo se aceptan valores del catálogo
RF-05 — IMSS e INFONAVIT con opción No aplica
Los campos IMSS e INFONAVIT dejarán de ser checkboxes binarios.
Cada campo debe ofrecer tres opciones:
- Sí
- No
- No aplica
UI recomendada:
- radio group por campo
- o select por campo
Valores lógicos:
- SI
- NO
- NO_APLICA
Persistencia en columnas actuales:
- tiene_imss = 1 si SI
- tiene_imss = 0 si NO
- tiene_imss = NULL si NO_APLICA
- tiene_infonavit = 1 si SI
- tiene_infonavit = 0 si NO
- tiene_infonavit = NULL si NO_APLICA
---
6. Requerimientos de Base de Datos
DB-01 — Beneficiarios: nombre estructurado
Agregar columnas a beneficiarios:
- nombres TEXT NOT NULL
- apellido_paterno TEXT NOT NULL
- apellido_materno TEXT NULL
Mantener:
- nombre TEXT NOT NULL
Uso:
- nombre seguirá siendo el campo legado/canónico para compatibilidad
- los nuevos campos serán fuente estructurada de verdad
DB-02 — Tutores: estudios
No requiere cambio estructural obligatorio si nivel_estudios ya es TEXT.
Sí requiere:
- validación de catálogo en backend
DB-03 — Tutores: IMSS/INFONAVIT triestado
Modificar columnas existentes:
- tiene_imss
- tiene_infonavit
Cambios requeridos:
- permitir NULL
- eliminar restricción estricta NOT NULL
- ajustar CHECK para permitir 0, 1 o NULL
DB-04 — Tutores: ingreso mensual
Sin migración obligatoria en esta iteración.
Regla:
- la columna actual puede seguir almacenando enteros aunque sea REAL
Recomendación posterior:
- migrar a INTEGER o NUMERIC(9,0)
DB-05 — Estudios: catálogo de obtención de silla
No requiere cambio de tipo si como_obtuvo_silla sigue siendo TEXT.
Sí requiere:
- validación cerrada en backend
- persistencia de códigos canónicos:
  - COMPRA
  - DONACION
---
7. Cambios en Contrato de API
Payload de creación/actualización del beneficiario
Antes:
{
  "beneficiario": {
    "nombre": "Juan Perez Lopez"
  }
}
Después:
{
  "beneficiario": {
    "nombres": "Juan",
    "apellido_paterno": "Perez",
    "apellido_materno": "Lopez"
  }
}
Regla de compatibilidad:
- el backend debe componer internamente nombre
- si existe compatibilidad temporal, puede aceptarse nombre legado solo durante migración, pero la forma objetivo es estructurada
Payload del tutor
nivel_estudios debe enviar código canónico:
{
  "nivel_estudios": "LICENCIATURA_INGENIERIA"
}
ingreso_mensual debe enviarse como entero:
{
  "ingreso_mensual": 12500
}
IMSS e INFONAVIT deben enviarse como estado lógico explícito:
{
  "imss_estatus": "NO_APLICA",
  "infonavit_estatus": "SI"
}
Nota:
El backend traducirá esos valores a las columnas actuales tiene_imss y tiene_infonavit.
Payload del estudio
como_obtuvo_silla debe enviar solo:
{
  "como_obtuvo_silla": "COMPRA"
}
o
{
  "como_obtuvo_silla": "DONACION"
}
---
## 8. Requerimientos de Frontend
### UI-01 — Nombre del beneficiario
Reemplazar `Nombre Completo` por tres inputs visibles.
Debe incluir:
- `required` donde aplique
- `maxlength`
- validación de patrón
- mensajes claros de error
### UI-02 — Estudios del tutor
Reemplazar input de texto por select en Tutor 1 y Tutor 2.
### UI-03 — Ingreso mensual
Mantener input tipo texto para formato visual, pero con lógica que:
- elimine todo excepto dígitos
- inserte separador de miles
- no permita punto decimal
### UI-04 — Cómo obtuvo la silla
Reemplazar input libre por select.
Debe seguir condicionado por “¿El paciente ha tenido silla previamente?”
### UI-05 — IMSS e INFONAVIT
Reemplazar checkboxes binarios por controles triestado.
No deben coexistir dos valores activos al mismo tiempo.
---
9. Requerimientos de Backend
BE-01 — Validación del nombre estructurado
Backend debe validar:
- presencia de nombres
- presencia de apellido_paterno
- optional apellido_materno
- regex por campo
- longitudes mínimas y máximas
- normalización centralizada
BE-02 — Composición de nombre legado
Backend debe construir beneficiarios.nombre concatenando los tres componentes ya normalizados.
BE-03 — Catálogo de estudios
Backend debe rechazar cualquier valor fuera del catálogo de nivel_estudios.
BE-04 — Ingreso mensual entero
Backend debe rechazar:
- decimales
- números negativos
- valores mayores a 999999
- strings no numéricos
BE-05 — Catálogo de obtención de silla
Backend debe:
- exigir catálogo cerrado cuando tuvo_silla_previa = true
- guardar NULL cuando tuvo_silla_previa = false
BE-06 — Traducción triestado IMSS/INFONAVIT
Backend debe mapear:
- SI -> 1
- NO -> 0
- NO_APLICA -> NULL
Y al leer borradores:
- 1 -> SI
- 0 -> NO
- NULL -> NO_APLICA
---
10. Requerimientos No Funcionales
- Toda validación debe existir en frontend y backend
- Backend sigue siendo fuente de verdad
- No debe romperse el flujo de borrador
- Los nuevos catálogos deben ser accesibles por teclado
- Los cambios deben ser compatibles con móvil
- La migración debe ser incremental y no destructiva
---
11. Casos Borde
- José debe aceptarse en UI y persistirse como JOSE
- María Fernanda debe aceptarse como nombre compuesto
- O'Brien debe rechazarse por contener apóstrofe
- 12345 en nombre debe rechazarse
- 12.5 en ingreso mensual debe rechazarse
- 12,500 en UI debe convertirse a 12500 en payload
- tuvo_silla_previa = false con como_obtuvo_silla = COMPRA debe guardar NULL
- IMSS No aplica debe persistirse como NULL
- apellido_materno vacío debe guardarse como NULL
---
12. Criterios de Aceptación
CA-01 — Nombre del beneficiario
- Se muestran tres campos separados
- No se aceptan números ni símbolos
- Se aceptan acentos en captura
- Se guarda en mayúsculas según política vigente
- beneficiarios.nombre queda concatenado correctamente
- beneficiarios.nombres, apellido_paterno, apellido_materno quedan persistidos de forma consistente
CA-02 — Estudios del tutor
- El usuario solo puede seleccionar una opción del catálogo
- Backend rechaza texto libre fuera de catálogo
- El borrador se recarga correctamente mostrando la opción seleccionada
CA-03 — Ingreso mensual
- No se puede escribir .
- No se pueden escribir letras o símbolos
- Se aplica separador de miles visual
- El payload envía entero limpio
- Backend rechaza decimales y valores fuera de rango
CA-04 — Cómo obtuvo la silla
- Solo aparecen Compra y Donación
- El campo solo es obligatorio cuando hubo silla previa
- Backend rechaza cualquier valor no catalogado
CA-05 — IMSS e INFONAVIT
- Cada campo permite Sí, No, No aplica
- El valor No aplica se persiste como NULL
- Al recargar borrador, el valor se muestra correctamente
---
13. Plan de Implementación Recomendado
1. Crear migración incremental para beneficiarios y triestado de IMSS/INFONAVIT.
2. Ajustar modelos Pydantic y validadores de socioeconomico.py.
3. Ajustar inserción/lectura de beneficiario y tutores.
4. Actualizar front/socioeconomico.html para nuevos campos y catálogos.
5. Ajustar serialización y rehidratación de borradores.
6. Agregar pruebas de validación backend.
7. Ejecutar validación manual del flujo:
   - login
   - selección de región
   - guardar borrador
   - reanudar borrador
   - completar estudio
---
14. Riesgos y Compatibilidad
- Separar nombre solo en UI sin migración de DB dejaría el sistema SEMÁNTICAMENTE inconsistente.
- Mantener booleans estrictos impediría representar No aplica.
- Mantener normalize_text() actual implica perder acentos en DB; esto es consistente con el estado actual, pero debe aceptarse explícitamente como decisión funcional.
---
15. Resultado Esperado
Al finalizar esta iteración:
- el formulario tendrá estructura más precisa
- el backend validará mejor los datos reales
- la DB podrá representar correctamente los nuevos estados requeridos
- se mantendrá compatibilidad razonable con el modelo actual sin reescribir la arquitectura