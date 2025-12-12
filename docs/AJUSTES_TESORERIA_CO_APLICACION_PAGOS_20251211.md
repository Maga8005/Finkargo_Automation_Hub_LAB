# Ajustes Requeridos - Tesorería Colombia Aplicación de Pagos

**Fecha de Reunión:** Diciembre 2024
**Participantes:** Tania Pineros, Daniel Restrepo, Juan
**Módulo:** Tesorería - Plantillas NetSuite Colombia
**Estado:** Pendiente de implementación

---

## Resumen Ejecutivo

Se identificaron múltiples problemas en la lógica de conversión del Historial de Pagos a plantilla NetSuite para Colombia. Los ajustes afectan principalmente el cálculo y ubicación del spread, el manejo de tasas de cambio según tipo de pago, y las cuentas contables según estado de recompra de la operación.

---

## Problemas Identificados

### 1. Línea Adicional de Spread Incorrecta

**Problema:** El sistema está creando una línea de spread separada para TODOS los pagos, cuando solo debería hacerlo para pagos "Pago en línea" donde el único concepto es CAPITAL.

**Comportamiento Actual:**
- Se está agregando una línea de SPREAD debajo de cada pago
- Las columnas Spread PA/FK/Supra están quedando vacías
- El spread no está siendo calculado correctamente

**Comportamiento Esperado:**
- Solo crear línea separada de SPREAD cuando:
  1. El pago es "Pago en línea"
  2. El único concepto con valor es CAPITAL
- En todos los demás casos, el spread debe ir en las columnas Spread PA/FK/Supra de la primera línea no-CAPITAL

### 2. Agrupación Incorrecta de Pagos (Payment Ref)

**Problema:** La referencia de pago generada (`payment_ref`) no diferencia correctamente pagos múltiples del mismo cliente en el mismo día.

**Comportamiento Actual:**
- Un cliente con múltiples pagos en el mismo día recibe la misma `payment_ref`
- Esto causa que los pagos se agrupen incorrectamente
- El spread se calcula de forma errónea al mezclar pagos diferentes

**Ejemplo Identificado:**
- Cliente: Marcando Soluciones
- Fecha: 4 de diciembre
- Realizó 2 pagos manuales el mismo día
- Sistema generó un solo documento para ambos pagos (incorrecto)

**Comportamiento Esperado:**
- Cada pago debe tener una `payment_ref` única
- Si la tasa de cambio (`exchangerate`) es diferente, se puede usar para diferenciar
- **Limitación conocida:** Si no hay ningún campo diferenciador (misma fecha, misma tasa), no hay forma de separar los pagos con el historial actual

**Acción Requerida (Largo Plazo):**
- El código de recaudo debe corregirse en el sistema origen para ser único por pago
- Tiempo estimado de corrección: ~3 meses

### 3. Cálculo de Spread Multi-Fila Incorrecto

**Problema:** Cuando un pago tiene múltiples filas (ej: una en USD y otra en COP), el spread debe calcularse sobre el TOTAL de todas las filas del mismo pago.

**Ejemplo:**
- Cliente: Cardiofit Store
- Pago 1: $200 USD (todo a capital) → Debe crear línea SPREAD
- Pago 2: $550.46 USD con múltiples conceptos
  - Fila 1 (USD): Total pagado ~$50
  - Fila 2 (COP): Total pagado ~$500
  - **Spread correcto:** ($50 + $500) × spread_rate = ~$27,600

**Comportamiento Actual:**
- El sistema desconecta las filas y calcula spread por fila individual
- Cada fila se trata como un pago independiente

**Comportamiento Esperado:**
- Agrupar filas por `payment_ref` (concatenado de cliente + fecha + moneda + cuenta_remitente + exchangerate)
- Sumar el `Total Pagado [USD]` de todas las filas del grupo
- Calcular spread una sola vez sobre el total
- Colocar el spread en una sola línea (no-CAPITAL preferentemente)

### 4. Tasa de Cambio según Tipo de Pago

**Problema:** La tasa de cambio se está aplicando a todos los pagos, pero solo debe aplicarse para pagos en línea.

**Reglas Correctas:**

| Tipo de Pago | Moneda | Campo `exchangerate` | Spread |
|--------------|--------|---------------------|--------|
| Pago en línea | USD | Tasa Fincargo (sin ajuste) | Spread FK o Spread PA |
| Pago en línea | COP | Tasa Fincargo - Spread = Tasa IMC | Spread FK o Spread PA |
| Manual | USD | **VACÍO** (NetSuite toma TRM automáticamente) | No aplica (es USD puro) |
| Manual | COP/Pesos | **VACÍO** (NetSuite toma TRM automáticamente) | Spread PA calculado |

**Cálculo de Spread para Pagos Manuales (COP):**
```
Spread = (Tasa Fincargo - Tasa Banco de la República) × Total Pagado USD
```

**Nota:** La tasa Fincargo y la tasa "en línea" están en el mismo campo del historial de pagos: `Tasa de cambio de FK/en línea`

### 5. Cuentas Contables (AR Account) según Estado de Recompra

**Problema:** No se está considerando si la operación ha sido recomprada para determinar las cuentas contables.

**Contexto:**
- Las operaciones pueden estar **cedidas** (NT) al patrimonio autónomo
- Las operaciones cedidas pueden ser **recompradas** por Fincargo Colombia

**Reglas de Cuentas AR:**

| Estado Operación | Concepto | Cuenta AR |
|-----------------|----------|-----------|
| Normal (no cedida) | CAPITAL | 302 |
| Normal (no cedida) | INTERESES | 258 |
| Normal (no cedida) | MORATORIOS | 258 |
| Normal (no cedida) | COSTOS_FIJOS | 258 |
| Normal (no cedida) | SEGUROS | 1387 |
| Cedida (NT) - No recomprada | CAPITAL | 304 |
| Cedida (NT) - No recomprada | INTERESES | 259 |
| Cedida (NT) - No recomprada | MORATORIOS | 259 |
| Cedida (NT) - No recomprada | COSTOS_FIJOS | 310 |
| Cedida (NT) - No recomprada | SEGUROS | 1474 |
| **Cedida pero RECOMPRADA** | CAPITAL | **302** |
| **Cedida pero RECOMPRADA** | INTERESES | **258** |
| **Cedida pero RECOMPRADA** | MORATORIOS | **258** |
| **Cedida pero RECOMPRADA** | COSTOS_FIJOS | **258** |
| **Cedida pero RECOMPRADA** | SEGUROS | **1387** |

**Acción Requerida:**
- Identificar el campo en el historial de pagos que indica si la operación está recomprada
- Cuando está recomprada, usar las cuentas de Fincargo Colombia (no las del patrimonio)

### 6. Spread No Calculado para Pagos Manuales

**Problema:** El sistema solo calcula spread para pagos en línea, pero también debe calcularse para pagos manuales que ingresan en COP (pesos).

**Pagos que DEBEN tener spread calculado:**
1. Pago en línea (cualquier moneda) → Spread FK o Spread PA según columna NT
2. Pago manual que ingresa a Bancolombia (COP) → Spread PA
3. Pago manual que ingresa a cuenta en pesos del patrimonio (COP) → Spread PA

**Pagos que NO deben tener spread:**
1. Pago manual que ingresa a cuenta de compensación del PEA en dólares → No aplica (es USD puro)

---

## Resumen de Cambios Requeridos

### Prioridad Alta (Críticos)

1. **Fix: Línea SPREAD solo para capital-only pago en línea**
   - Verificar lógica en `_is_capital_only_pago_en_linea()`
   - Asegurar que spread va a columnas cuando hay múltiples conceptos

2. **Fix: Tasa de cambio vacía para pagos manuales**
   - Si `medio_pago` = "Manual" → `exchangerate = None`
   - Solo aplicar tasa cuando `medio_pago` contiene "pago en l" (línea)

3. **Fix: Cálculo de spread para pagos manuales COP**
   - Fórmula: `(tasa_fincargo - tasa_TRM) × total_pagado_usd`
   - Aplicar a Spread PA
   - **Nota:** Requiere obtener la tasa TRM del Banco de la República para la fecha del pago

4. **Fix: Agrupación de spread multi-fila**
   - Sumar `Total Pagado [USD]` de todas las filas del mismo `payment_ref`
   - Calcular spread sobre el total agregado
   - Colocar en una sola línea de salida

### Prioridad Media

5. **Feature: Considerar estado de recompra**
   - Identificar campo que indica recompra en historial
   - Si recomprada → usar cuentas Fincargo Colombia (302, 258, 1387)
   - Si cedida no recomprada → usar cuentas patrimonio (304, 259, 310, 1474)

### Limitaciones Conocidas

6. **Limitación: Payment Ref no única para pagos múltiples mismo día**
   - Sin solución inmediata disponible
   - Depende de corrección del código de recaudo en sistema origen (~3 meses)
   - Workaround actual: usar `exchangerate` diferente para diferenciar si aplica

---

## Campos del Historial de Pagos Relevantes

| Campo | Descripción | Uso |
|-------|-------------|-----|
| `Médio de pago` | "Manual" o "Pago en línea" | Determina lógica de tasa y spread |
| `Tasa de cambio de FK/en línea` | Tasa Fincargo | Para cálculo de spread |
| `Total pagado [USD]` | Monto total en USD | Base para cálculo de spread |
| `NT` | Indica operación cedida | Routing a cuentas AR |
| `[Campo recompra TBD]` | Indica si está recomprada | Override de cuentas AR |
| `Cuenta Remitente` | Cuenta bancaria origen | Lookup de account ID |
| `Moneda` | COP, USD, etc. | Lógica de spread |

---

## Próximos Pasos

1. [ ] Revisar y confirmar campo que indica estado de recompra
2. [ ] Obtener o calcular tasa TRM del Banco de la República por fecha
3. [ ] Implementar ajustes en `payment_template_service.py`
4. [ ] Actualizar catálogo de cuentas AR con lógica de recompra
5. [ ] Pruebas con archivo de ejemplo proporcionado
6. [ ] Validación con equipo de Tesorería (Tania, Juan)
