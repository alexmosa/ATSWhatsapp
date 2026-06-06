Asunto: Presentación de Candidatos Finalistas – {{ vacante }}

Estimado/a {{ hiring_manager }},

Tras concluir la etapa de sourcing y evaluación profunda mediante entrevistas STAR, te presento formalmente a los {{ candidatos|length }} candidatos finalistas para la posición de {{ vacante }}.

A continuación, encontrarás el resumen ejecutivo de sus perfiles:

{% for c in candidatos %}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Candidato {{ loop.index }}: {{ c.nombre }}

• Puesto Actual: {{ c.puesto_actual or 'No registrado' }} en {{ c.empresa_actual or 'No registrada' }}
• Años de Experiencia: {{ c.anos_experiencia or 'No registrado' }} años.
• Expectativa Económica: ${{ c.expectativa_salarial or 'Por definir' }} {{ c.moneda_salarial }} mensuales {{ c.salario_tipo }}.
• Disponibilidad / Preaviso: {{ c.disponibilidad or 'Por confirmar' }}.

👍 Fortalezas Clave:
{% for f in c.fortalezas or [] %}
  - {{ f }}
{% else %}
  - Sin fortalezas registradas en el ATS.
{% endfor %}

⚠️ Áreas de Oportunidad / Riesgos:
{% for r in c.areas_oportunidad or [] %}
  - {{ r }}
{% else %}
  - Sin áreas de oportunidad registradas en el ATS.
{% endfor %}

💬 Conclusión del Reclutador: {{ c.notas_reclutador or 'Pendiente de evaluación final.' }}

{% endfor %}
