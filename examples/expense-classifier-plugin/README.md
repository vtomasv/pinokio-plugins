# Expense Classifier Plugin

Plugin para clasificación automática de gastos empresariales usando IA local. Categoriza transacciones, genera visualizaciones y exporta reportes, todo sin conexión a internet.

## Funcionalidades

**Clasificación automática**: Analiza descripciones de gastos y los asigna a categorías como Operaciones, Marketing, Impuestos, Personal, Servicios, etc.

**Corrección manual**: Permite al usuario revisar y corregir las clasificaciones sugeridas por la IA con una interfaz intuitiva.

**Visualizaciones**: Genera gráficos de distribución de gastos por categoría y período.

**Exportación**: Genera reportes en formato CSV con los gastos clasificados y totales por categoría.

## Categorías de Gastos

| Categoría | Ejemplos |
|-----------|---------|
| Operaciones | Alquiler, servicios básicos, mantenimiento |
| Personal | Sueldos, honorarios, capacitación |
| Marketing | Publicidad, diseño, eventos |
| Tecnología | Software, hardware, hosting |
| Impuestos | IVA, impuesto a la renta, tasas |
| Servicios Profesionales | Contabilidad, legal, consultoría |
| Otros | Gastos no clasificados |

## Patrones Demostrados

**Clasificación con modelo liviano**: Usa `llama3.2:1b` para clasificación (tarea simple), optimizando el uso de RAM en hardware limitado.

**Procesamiento por lotes**: Clasifica hasta 20 gastos por llamada al LLM para eficiencia.

**Corrección iterativa**: El usuario puede confirmar o corregir cada clasificación, y el sistema aprende las preferencias guardándolas en disco.

## Instalación

1. Copia este directorio a `~/pinokio/api/expense-classifier-plugin/`.
2. Abre Pinokio y haz clic en "Instalar" (requiere mínimo 2GB RAM).
3. Una vez instalado, haz clic en "Iniciar".

## Uso

1. Ingresa los gastos manualmente o pega una lista de transacciones.
2. Haz clic en "Clasificar" para que la IA asigne categorías automáticamente.
3. Revisa las clasificaciones y corrige las que sean incorrectas.
4. Visualiza el resumen con gráficos de distribución.
5. Exporta el reporte en CSV.

> **Nota**: Este es un ejemplo de referencia. Para el plugin completo de producción del proyecto CCS, consulta el repositorio principal del proyecto.
