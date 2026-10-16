from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from jinja2 import Environment, BaseLoader

from bi_analysis.rag.pipeline import create_rag_pipeline
from bi_analysis.database.session import get_db_session
from bi_analysis.database.models import Report, ExtractedItem, SourceType, ContentType
from bi_analysis.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


REPORT_TEMPLATES = {
    "executive_summary": """
# Relatório Executivo: {{ title }}

**Período:** {{ period_start }} a {{ period_end }}
**Gerado em:** {{ generated_at }}
**Total de itens analisados:** {{ total_items }}

## Resumo
{{ summary }}

## Principais Insights
{% for insight in insights %}
- {{ insight }}
{% endfor %}

## Métricas Principais
{% for metric, value in metrics.items() %}
- **{{ metric }}:** {{ value }}
{% endfor %}

## Recomendações
{% for rec in recommendations %}
- {{ rec }}
{% endfor %}
""",
    "sentiment_analysis": """
# Análise de Sentimento: {{ title }}

**Período:** {{ period_start }} a {{ period_end }}
**Fonte:** {{ source_type }}
**Total de comentários/posts:** {{ total_items }}

## Distribuição de Sentimento
{% for sentiment, count in sentiment_distribution.items() %}
- **{{ sentiment }}:** {{ count }} ({{ "%.1f"|format(count/total_items*100) }}%)
{% endfor %}

## Tópicos Principais
{% for topic in topics %}
- **{{ topic.name }}:** {{ topic.count }} menções (Sentimento médio: {{ topic.avg_sentiment }})
{% endfor %}

## Exemplos por Sentimento
### Positivos
{% for ex in positive_examples %}
- {{ ex }}
{% endfor %}

### Negativos
{% for ex in negative_examples %}
- {{ ex }}
{% endfor %}

### Neutros
{% for ex in neutral_examples %}
- {{ ex }}
{% endfor %}
""",
    "trend_report": """
# Relatório de Tendências: {{ title }}

**Período:** {{ period_start }} a {{ period_end }}
**Frequência:** {{ frequency }}

## Evolução Temporal
{% for period, count in timeline.items() %}
- **{{ period }}:** {{ count }} itens
{% endfor %}

## Top Hashtags/Términos
{% for term, count in top_terms.items() %}
- **{{ term }}:** {{ count }}
{% endfor %}

## Picos de Atividade
{% for peak in peaks %}
- **{{ peak.date }}:** {{ peak.count }} itens - {{ peak.reason }}
{% endfor %}
""",
    "custom": """
# {{ title }}

{{ custom_content }}
""",
}


class ReportGenerator:
    def __init__(self):
        self.rag = create_rag_pipeline()
        self.db = get_db_session()
        self.jinja_env = Environment(loader=BaseLoader())

    def generate_report(
        self,
        title: str,
        report_type: str,
        filters: Dict[str, Any],
        template: str = None,
        custom_prompt: str = None,
    ) -> Report:
        where = self._build_where_filter(filters)
        items_count = self._count_items(where)
        
        if items_count == 0:
            raise ValueError("Nenhum item encontrado com os filtros especificados")

        context_query = self._build_context_query(filters)
        rag_response = self.rag.query(context_query, where=where)
        
        template_content = template or REPORT_TEMPLATES.get(report_type, REPORT_TEMPLATES["custom"])
        template_obj = self.jinja_env.from_string(template_content)
        
        template_vars = self._prepare_template_vars(
            title=title,
            report_type=report_type,
            filters=filters,
            rag_response=rag_response,
            items_count=items_count,
        )
        
        generated_content = template_obj.render(**template_vars)
        
        report = Report(
            title=title,
            report_type=report_type,
            template=template,
            parameters=filters,
            generated_content=generated_content,
            status="generated",
            generated_at=datetime.utcnow(),
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report

    def _build_where_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        where = {}
        if filters.get("source_type"):
            where["source_type"] = filters["source_type"]
        if filters.get("content_type"):
            where["content_type"] = filters["content_type"]
        if filters.get("author"):
            where["author"] = filters["author"]
        if filters.get("date_from") or filters.get("date_to"):

            pass
        return where if where else None

    def _count_items(self, where: Dict[str, Any]) -> int:
        query = self.db.query(ExtractedItem)
        if where:
            if where.get("source_type"):
                query = query.filter(ExtractedItem.source_type == where["source_type"])
            if where.get("content_type"):
                query = query.filter(ExtractedItem.content_type == where["content_type"])
            if where.get("author"):
                query = query.filter(ExtractedItem.author == where["author"])
        return query.count()

    def _build_context_query(self, filters: Dict[str, Any]) -> str:
        parts = ["Analise os dados extraídos"]
        if filters.get("source_type"):
            parts.append(f"da fonte {filters['source_type']}")
        if filters.get("content_type"):
            parts.append(f"do tipo {filters['content_type']}")
        if filters.get("date_from") and filters.get("date_to"):
            parts.append(f"no período de {filters['date_from']} a {filters['date_to']}")
        parts.append("e gere um relatório com insights, métricas e recomendações.")
        return " ".join(parts)

    def _prepare_template_vars(
        self,
        title: str,
        report_type: str,
        filters: Dict[str, Any],
        rag_response,
        items_count: int,
    ) -> Dict[str, Any]:
        now = datetime.utcnow()
        return {
            "title": title,
            "generated_at": now.strftime("%d/%m/%Y %H:%M"),
            "period_start": filters.get("date_from", "Início dos dados"),
            "period_end": filters.get("date_to", "Fim dos dados"),
            "total_items": items_count,
            "source_type": filters.get("source_type", "Todas"),
            "summary": rag_response.answer[:500] + "..." if len(rag_response.answer) > 500 else rag_response.answer,
            "insights": self._extract_insights(rag_response.answer),
            "metrics": self._extract_metrics(rag_response.answer),
            "recommendations": self._extract_recommendations(rag_response.answer),
            "sentiment_distribution": {},
            "topics": [],
            "positive_examples": [],
            "negative_examples": [],
            "neutral_examples": [],
            "timeline": {},
            "top_terms": {},
            "peaks": [],
            "frequency": filters.get("frequency", "Diária"),
            "custom_content": rag_response.answer,
        }

    def _extract_insights(self, text: str) -> List[str]:
        insights = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "• ", "* ")) and len(line) > 10:
                insights.append(line[2:].strip())
        return insights[:5]

    def _extract_metrics(self, text: str) -> Dict[str, str]:
        metrics = {}
        return metrics

    def _extract_recommendations(self, text: str) -> List[str]:
        recs = []
        for line in text.split("\n"):
            line = line.strip().lower()
            if any(kw in line for kw in ["recomend", "suger", "deve", "precisa"]):
                recs.append(line)
        return recs[:5]


def generate_report(
    title: str,
    report_type: str,
    filters: Dict[str, Any],
    template: str = None,
) -> Report:
    generator = ReportGenerator()
    return generator.generate_report(title, report_type, filters, template)
